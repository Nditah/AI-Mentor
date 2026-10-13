# AI Mentor — RBAC and ABAC Matrix (v2)

| Field | Value |
| --- | --- |
| Document | RBAC and ABAC Matrix |
| Version | 2.0 |
| Date | 13 October 2026 |
| Status | Approved direction. Target model; not built. From R1 this file is generated from the seeded role–permission data and CI fails on drift (ADR 0016) |
| Owner | Security Architecture, with Product (one owner per app) |
| Related | [README.md](README.md) (role IDs, scopes, permission format), [09-security-model.md](09-security-model.md), [ADR 0016](../adr/0016-scoped-rbac-abac.md), [ADR 0015](../adr/0015-organisation-tenancy.md), ADR 0021, ADR 0025, [../Security-Compliance.md](../Security-Compliance.md) §4–5 (v1, superseded) |

## Change record

| Area | What changed | Why | Impacted systems | Implementation implications |
| --- | --- | --- | --- | --- |
| Roles | Three ranked roles replaced by 22 scoped human roles plus `system` | Five apps, many tenants, org-unit hierarchy (ADR 0013, 0015) | `authz`, every router, all five apps | Seed `authz.roles`; remove the rank in `access.py` after migration |
| Permissions | Named permissions `<context>.<resource>:<action>` grouped by bounded context, each listed once | Explicit sets per role (v1 §4.2 recommendation, ADR 0016) | `authz.permissions`, `require()` | Every route names one permission; coverage test |
| Matrices | One matrix per app instead of one matrix for one app | Each app has its own audience and workflows | App route guards (render only), API | Matrix rows carry the permission so they are machine-checkable |
| Data visibility | Cross-app visibility of learning record vs academic record, personal vs managed | ADR 0021 | `learning`, `assessment`, `analytics`, `reporting` | Visibility enforced in queries, not in UI |
| ABAC | Condition catalogue ABAC-01 to ABAC-30 | Conditions that roles cannot express | Policy engine | Each condition is a tested predicate |
| Governance | Separation of duties, delegation table, custom role policy | Prevent self-escalation and single-person control of sensitive outcomes | `authz` | Delegation table is seed data, checked at grant time |
| Migration | v1 roles mapped to v2 assignments; v1 routes mapped to permissions | Expand, backfill, switch, contract (ADR 0016) | `identity.users.role`, RLS policies | Shim keeps `is_allowed` working until every router uses `require` |

## Relationship to v1 documents

This document and [09-security-model.md](09-security-model.md) **supersede** `Security-Compliance.md` §4 (Authorisation model) and §5 (RBAC matrix). v1 rules AZ-1 to AZ-7 remain valid and are restated for scoped roles in 09 §5. The v1 legend (§5) is reused unchanged and extended with scope symbols. v1 capability rows map to the Learner App and Content Studio matrices below; v1 "Admin" columns map to `platform_admin` plus the workspace roles in the migration table (§10). `Security.md` keeps describing what the build does today.

## Contents

0. [Current state](#0-current-state)
1. [How to read this document](#1-how-to-read-this-document)
2. [Role catalogue](#2-role-catalogue)
3. [Permission catalogue](#3-permission-catalogue)
4. [Matrices per application](#4-matrices-per-application)
5. [Cross-app data visibility](#5-cross-app-data-visibility)
6. [ABAC condition catalogue](#6-abac-condition-catalogue)
7. [Separation of duties](#7-separation-of-duties)
8. [Delegation rules](#8-delegation-rules)
9. [Default role templates and custom roles](#9-default-role-templates-and-custom-roles)
10. [Migration and test requirements](#10-migration-and-test-requirements)

---

## 0. Current state

Today `backend/app/domain/access.py` ranks `student` (1), `instructor` (2), and `admin` (3). Every `/api/v1/admin/*` route requires at least `instructor`; services require `admin` for users, configuration, providers, and the audit log. There are no permissions, scopes, tenants, or workspaces. Everything below is target design, introduced from R1 (platform and consumer organisation) to R4 (custom roles).

---

## 1. How to read this document

**Legend** (v1 symbols first, scope symbols added):

| Symbol | Meaning |
| --- | --- |
| ✅ | Allowed at the scope of the assignment held |
| 🔶 | Own records only |
| 📊 | Aggregated or de-identified only (k ≥ 10 where 09 PV-10 applies) |
| 🎫 | With recorded reason (ticket or case id), audited |
| ❌ | Denied |
| 👥 | Own cohorts only: cohorts where the person is listed in `classroom.cohort_staff` |
| 🌳 | Own org-unit subtree: the campus or department held, and every unit below it |
| 🔐 | Step-up required: second factor verified within 15 minutes (ABAC-09) |
| 🤝 | Takes effect only after a second person approves (§7) |

Symbols combine: `👥🔐` means own cohorts, with step-up. A blank cell never appears; denial is always ❌.

Rules for reading the matrices:

1. A cell describes what the role grants **on its own**. A person's effective rights are the union of all their assignments, each limited to its own scope, minus explicit denies.
2. Every row names its permission. The API enforces the permission and its ABAC conditions; the app only decides what to render.
3. A role at an outer scope applies to every unit below it (README). `instructor` assigned at a department behaves as 🌳 for that department; assigned at a cohort it behaves as 👥.
4. The **app audience** column of §2 is the app that opens for the role. `platform.*` permissions are refused unless the token's `azp` is the Admin App (ABAC-08).
5. "Tier" and "Licence" columns show entitlements (ABAC-12, ABAC-23), not roles.

---

## 2. Role catalogue

All role IDs from the README. MFA column: **Required** means the app refuses sign-in without a second factor; **Policy** means the organisation decides; **Step-up** lists when freshness ≤ 15 minutes is needed beyond the sign-in rule.

| Role ID | Scope types | App | MFA | Assignable by (§8) | Constraints |
| --- | --- | --- | --- | --- | --- |
| `learner` | organisation, cohort | Learner | Optional; Policy for managed accounts | Self (consumer organisation, enrolment code), `instructor`, `lead_instructor`, `department_admin`, `campus_admin`, `org_admin`, `org_owner`, SCIM, JIT, LTI | Cannot be held in a cohort where the person holds a staff role (SoD-5) |
| `teaching_assistant` | cohort | Instructor | Policy (SHOULD) | `lead_instructor`, `department_admin`, `campus_admin`, `org_admin`, `org_owner`, SCIM group mapping | No release or override unless a time-boxed delegation is granted (AZ-21) |
| `instructor` | cohort, department | Instructor | Policy (SHOULD); Step-up: grade override | `lead_instructor`, `department_admin`, `campus_admin`, `org_admin`, `org_owner`, SCIM group mapping | — |
| `lead_instructor` | cohort, department, campus | Instructor | Policy (SHOULD); Step-up: override approval | `department_admin`, `campus_admin`, `org_admin`, `org_owner` | Not grantable by SCIM, JIT, or LTI |
| `department_admin` | department | Institution | Policy (SHOULD); Step-up: role grants | `campus_admin`, `org_admin`, `org_owner` | — |
| `campus_admin` | campus | Institution | Policy (SHOULD); Step-up: role grants | `org_admin`, `org_owner` | — |
| `org_admin` | organisation | Institution | Required (or IdP-asserted MFA); Step-up: SSO, role grants, exports | `org_owner` | — |
| `org_owner` | organisation | Institution | Required (or IdP-asserted MFA); Step-up: all governance actions | `org_owner`; `platform_admin` at organisation creation or recovery (🎫) | At least one per organisation (AZ-17); at most 5 per organisation |
| `org_billing_manager` | organisation | Institution | Policy (SHOULD); Step-up: payment method | `org_owner` | — |
| `org_report_viewer` | organisation, campus, department | Institution | Policy | `department_admin` (department), `campus_admin` (campus and below), `org_admin`, `org_owner` | Read-only; no per-learner exports |
| `org_compliance_officer` | organisation | Institution | Required; Step-up: DSAR execution, audit export | `org_owner` | SHOULD be held by at least one person in every non-consumer organisation |
| `content_author` | workspace | Content Studio | Required in `master`; Policy in `org` | `platform_admin` (master); `org_owner`, `org_admin` (org workspace) | — |
| `content_reviewer` | workspace | Content Studio | Required in `master`; Policy in `org` | As `content_author` | Cannot approve own or last-edited work (SoD-1) |
| `content_publisher` | workspace | Content Studio | Required; Step-up: publish, archive, restore, takedown | `platform_admin` (master); `org_owner` (org workspace) | — |
| `knowledge_steward` | workspace | Content Studio | Required in `master`; Step-up: concept graph changes in `master` | `platform_admin` (master); `org_owner` (org workspace) | — |
| `localisation_editor` | workspace | Content Studio | Required in `master`; Policy in `org` | As `content_author` | Limited to assigned locales (ABAC-24) |
| `support_agent` | platform | Admin | Required | `platform_admin` | Every read of an account needs a ticket (ABAC-11) |
| `finance_admin` | platform | Admin | Required; Step-up: refunds, licence edits | `platform_admin` | Refunds above threshold 🤝 (SoD-8) |
| `ai_admin` | platform | Admin | Required; Step-up: routes, prompt releases, guardrails | `platform_admin` | Marking and safety prompt releases 🤝 (SoD-7) |
| `platform_operator` | platform | Admin | Required; Step-up: all `platform.*` writes | `platform_admin` | — |
| `security_auditor` | platform | Admin | Required | `platform_admin` | Cannot be held with `platform_admin`, `platform_operator`, or `ai_admin` (SoD-3) |
| `platform_admin` | platform | Admin; Content Studio (read, emergency takedown) | Required; Step-up: all sensitive permissions | `platform_admin` | At least one, at most 5 (AZ-17); not self-assignable (SoD-4) |
| `system` | platform | none | Not applicable (workload identity) | Deployment configuration only, reviewed in code | One function per principal (09 AU-24) |

---

## 3. Permission catalogue

Each permission appears once. Context is the bounded-context module (README), except that the `ai_gateway` module uses the context `ai` and the `config` module uses the context `platform`, as in the README examples. **S** marks a sensitive permission: always written to the decision log and, unless stated otherwise in §2, subject to step-up (ABAC-09). README examples are marked (R).

### 3.1 identity

| Permission | S | Description |
| --- | --- | --- |
| `identity.profile:edit` | | Edit own profile and preferences |
| `identity.account:read` | | View accounts (name, email, status, memberships) within scope |
| `identity.account:create` | | Create a managed account in the active tenant |
| `identity.account:suspend` | S | Suspend or reactivate an account; organisation scope reaches only managed accounts of that organisation |
| `identity.account:export` | S | Run a data export on another person's behalf |
| `identity.account:erase` | S | Execute erasure on another person's behalf |
| `identity.session:revoke` | | Revoke another person's sessions |
| `identity.mfa:reset` | S | Reset a person's second factor after identity proofing |

### 3.2 authz

| Permission | S | Description |
| --- | --- | --- |
| `authz.role_assignment:read` | | List role assignments within scope |
| `authz.role_assignment:grant` | S | Grant a role at a scope, subject to §8 |
| `authz.role_assignment:revoke` | S | Revoke a role assignment, subject to §8 and AZ-17 |
| `authz.policy:edit` | S | Switch built-in policy conditions for the organisation (rows in `authz.policies`) |
| `authz.decision_log:read` | | Read authorisation decisions within scope |
| `authz.custom_role:edit` | S | Define custom roles from permission subsets (R4, §9) |

### 3.3 tenancy

| Permission | S | Description |
| --- | --- | --- |
| `tenancy.organisation:create` | S | Create an organisation and its first `org_owner` |
| `tenancy.organisation:read` | | Read organisation details |
| `tenancy.organisation:edit` | | Edit name, kind, contact, locale defaults |
| `tenancy.organisation:suspend` | S | Suspend or reactivate an organisation |
| `tenancy.organisation:delete` | S | Start organisation deletion (09 TI-14) |
| `tenancy.org_unit:edit` | | Create, rename, move, and archive campuses and departments |
| `tenancy.membership:read` | | List members and membership status within scope |
| `tenancy.membership:invite` | | Invite people by email |
| `tenancy.membership:import` | | Bulk import members from CSV |
| `tenancy.membership:end` | S | Suspend or end a membership |
| `tenancy.enrolment_code:create` | | Create and revoke enrolment codes |
| `tenancy.sso_connection:configure` (R) | S | Configure SSO for an organisation |
| `tenancy.domain:verify` | S | Claim and verify an email domain |
| `tenancy.custom_domain:configure` | S | Configure a white-label app domain (R4) |
| `tenancy.branding:edit` | | Edit colour tokens, logo, and display name |
| `tenancy.org_policy:edit` | S | Edit organisation policies (MFA, retention within bounds, leaderboard opt-outs, persona options, LTI role mapping) |

### 3.4 classroom

| Permission | S | Description |
| --- | --- | --- |
| `classroom.cohort:read` | | View cohorts, their members, staff, and schedules |
| `classroom.cohort:create` (R) | | Create a cohort |
| `classroom.cohort:edit` | | Edit cohort details and settings |
| `classroom.cohort:archive` | | Archive a cohort |
| `classroom.cohort_member:add` | | Add an existing member to a cohort |
| `classroom.cohort_member:remove` | | Remove a learner from a cohort |
| `classroom.cohort_member:import` (R) | | Bulk import learners into a cohort |
| `classroom.cohort_staff:assign` | S | Add or remove instructors and TAs on a cohort (creates the role assignment, subject to §8) |
| `classroom.cohort_plan:edit` | | Edit a cohort plan and its items |
| `classroom.cohort_plan:schedule` (R) | | Schedule a learning journey for a cohort |
| `classroom.live_session:edit` | | Create and edit live sessions |
| `classroom.attendance:record` | | Record attendance |
| `classroom.attendance:read` | | Read attendance |
| `classroom.risk_signal:read` | | Read risk signals with evidence |
| `classroom.intervention:create` | | Record an intervention for a learner |

### 3.5 learning

| Permission | S | Description |
| --- | --- | --- |
| `learning.catalogue:read` | | Browse published courses and paths available in the tenant |
| `learning.lesson:study` | | Open published lessons and record completion |
| `learning.practice:use` | | Use practice: quizzes, flashcards, daily challenges, coding lab |
| `learning.enrolment:create` (R) | | Enrol a learner (self, or others within scope) |
| `learning.enrolment:withdraw` | | Withdraw an enrolment |
| `learning.progress:read` | | Read another person's progress and mastery within scope |
| `learning.passport:export` | | Export own learning passport |

### 3.6 assessment

| Permission | S | Description |
| --- | --- | --- |
| `assessment.assessment:read` | | Read assessments and items, including secure items, within scope |
| `assessment.assessment:create` | | Create an assessment |
| `assessment.assessment:edit` | | Edit an assessment, its items, and answer keys |
| `assessment.rubric:edit` | | Create and edit rubrics |
| `assessment.assignment:publish` | | Issue an assessment to a cohort or learner with dates |
| `assessment.assignment:edit` | | Change dates, attempts, and grading settings |
| `assessment.integrity_mode:set` | | Turn integrity mode on or off for an assignment |
| `assessment.accommodation:edit` | | Grant accommodations (extra time, attempts) |
| `assessment.submission:submit` | | Submit a response to an assignment |
| `assessment.submission:read` | | Read submissions within scope |
| `assessment.submission:mark` (R) | | Mark a submission, including accepting an AI proposal |
| `assessment.ai_marking:request` | | Request AI-proposed marks for submissions |
| `assessment.grade:read` | | Read grades (learners: own released grades only) |
| `assessment.grade:override` (R) | S | Override a grade, including an AI-proposed grade |
| `assessment.grade_override:approve` | S | Approve another person's override when policy requires (ABAC-16) |
| `assessment.grade:release` (R) | S | Release grades to learners (logged; step-up not required) |
| `assessment.grade:appeal` | | Request a human regrade of own grade |
| `assessment.appeal:decide` | | Decide an appeal |
| `assessment.gradebook:export` | S | Export a gradebook |

### 3.7 content

| Permission | S | Description |
| --- | --- | --- |
| `content.item:read` | | Read lessons, modules, courses, and paths in every workflow state in the workspace |
| `content.item:create` | | Create a draft item |
| `content.item:edit` | | Edit a draft |
| `content.item:generate` | | Generate an AI draft from sources |
| `content.item:submit` | | Submit a draft for review |
| `content.item:review` | | Approve, or request changes on, an item in review |
| `content.course:publish` (R) | S | Publish a course release |
| `content.path:publish` | S | Publish a learning path release |
| `content.release:schedule` | S | Schedule a release |
| `content.release:archive` | S | Archive a release |
| `content.release:restore` | S | Restore a previous version as a new version |
| `content.item:take_down` | S | Take down a published lesson, module, course, or path from every release for rights, legal, or safety reasons (09 CS-7); in `master` a publisher's takedown needs `platform_admin` approval (SoD-11) |
| `content.overlay:edit` | | Create and edit overlays for a cohort or organisation |
| `content.derived_course:create` | | Copy a master release into an org workspace |
| `content.translation:edit` | | Translate content for assigned locales |
| `content.translation:approve` | | Approve a translation (`translation_status = approved`) |
| `content.workspace:create` | S | Provision an `org` workspace for a licensed organisation |

### 3.8 knowledge

| Permission | S | Description |
| --- | --- | --- |
| `knowledge.asset:read` | | Read knowledge assets, the taxonomy, and the concept graph in the workspace |
| `knowledge.asset:upload` | | Upload a draft knowledge asset |
| `knowledge.asset:edit` | | Edit asset metadata, rights, and versions |
| `knowledge.asset:take_down` | S | Take down an asset for rights or legal reasons (09 CS-7) |
| `knowledge.taxonomy:edit` | | Edit the taxonomy and controlled vocabularies |
| `knowledge.concept:edit` | | Create and edit concepts |
| `knowledge.concept_relation:edit` (R) | | Edit the knowledge graph |
| `knowledge.metadata_schema:edit` | | Edit the metadata schema |

### 3.9 retrieval, tutor, personalisation

| Permission | S | Description |
| --- | --- | --- |
| `retrieval.document:upload` | | Upload a personal research document for analysis |
| `retrieval.ingestion_job:read` | | View ingestion jobs and their flags |
| `retrieval.index:rebuild` | S | Rebuild or re-embed an index |
| `retrieval.chunk:quarantine` | | Quarantine flagged chunks pending review |
| `tutor.conversation:use` | | Talk to the mentor in any enabled mode |
| `tutor.solution:disclose` | | Receive worked solutions from the mentor (denied in integrity mode, ABAC-07) |
| `tutor.persona:select` | | Choose a mentor persona from allowed options |
| `tutor.persona:configure` | S | Define persona options (a prompt release) |
| `tutor.conversation:read` | S | Read another person's tutor transcripts (🎫, ABAC-26) |
| `tutor.flagged_message:review` | | Review the moderation queue |
| `personalisation.dimension:edit` | | Adjust own five dimensions within locks |
| `personalisation.dimension_lock:edit` | | Lock or bound a dimension for a cohort or organisation |
| `personalisation.learner_model:read` | | Read another person's learner model within scope |

### 3.10 gamification, analytics, reporting

| Permission | S | Description |
| --- | --- | --- |
| `gamification.leaderboard:read` | | View leaderboards the person may see (ABAC-28) |
| `gamification.leaderboard:configure` | | Configure institution and cohort boards within policy |
| `gamification.visibility:edit` | | Opt out of boards or set a handle |
| `gamification.competition:create` | | Create a competition or challenge |
| `gamification.badge:define` | | Define badges and titles |
| `gamification.entry:hold` | | Hold or remove a leaderboard entry for review (fraud) |
| `gamification.xp:adjust` | S | Correct an XP ledger (compensating entry) |
| `analytics.dashboard:read` | | View aggregated dashboards within scope |
| `analytics.benchmark:read` | | View de-identified cross-tenant benchmarks |
| `reporting.report:read` | | Run and view reports within scope |
| `reporting.report:create` | | Define a custom report |
| `reporting.report:schedule` | | Schedule recurring reports |
| `reporting.export:create` | S | Export learner-level data (CSV, XLSX) |
| `reporting.compliance_report:read` | | View compliance reports (consent, retention, DSAR, access) |

### 3.11 notification, messaging, search, i18n

| Permission | S | Description |
| --- | --- | --- |
| `notification.preference:edit` | | Edit own notification preferences |
| `notification.template:edit` | | Edit notification templates (platform: all; organisation: overrides of allowed fields) |
| `notification.broadcast:send` | S | Send a platform-wide notice |
| `messaging.message:send` | | Send direct messages within scope |
| `messaging.announcement:create` | | Post announcements to cohorts or org units |
| `messaging.discussion:moderate` | | Hide posts and lock threads |
| `search.person:query` | | Search people within scope |
| `search.index:rebuild` | S | Rebuild search indexes |
| `i18n.message_catalogue:edit` | | Edit UI message catalogues |

### 3.12 commerce, integration

| Permission | S | Description |
| --- | --- | --- |
| `commerce.subscription:manage` | | Manage a consumer subscription: learners their own; `finance_admin` any, at platform scope |
| `commerce.licence:read` | | View licences, seats, and usage |
| `commerce.licence:edit` | S | Create or amend an organisation licence |
| `commerce.seat:assign` | | Assign and release seats |
| `commerce.invoice:read` | | View invoices |
| `commerce.payment_method:edit` | S | Change the organisation's payment method |
| `commerce.plan:edit` | S | Edit consumer plans and prices |
| `commerce.refund:issue` | S | Issue refunds |
| `integration.lti_platform:configure` | S | Register LTI platforms and deployments |
| `integration.scim_client:configure` | S | Issue, rotate, and revoke SCIM tokens and group mappings |
| `integration.oneroster_sync:configure` | S | Configure OneRoster sync |
| `integration.webhook_endpoint:configure` | S | Configure outbound webhooks |
| `integration.xapi_export:configure` | | Configure xAPI or cmi5 export to an LRS |
| `integration.api_client:configure` | S | Register partner API clients (R5) |

### 3.13 ai, audit, platform

| Permission | S | Description |
| --- | --- | --- |
| `ai.model:register` | S | Add or retire a model in the registry |
| `ai.model_route:edit` (R) | S | Change model routing |
| `ai.prompt_release:publish` | S | Publish a prompt or persona release after its evaluation gate |
| `ai.guardrail:edit` | S | Change guardrail settings |
| `ai.evaluation:run` | | Run evaluation suites |
| `ai.usage:read` | | View AI usage and cost |
| `audit.log:read` (R) | S | Read audit logs at the scope held |
| `audit.log:export` | S | Export audit logs |
| `audit.data_access_log:read` | S | Read the data access log |
| `audit.security_event:read` | | Read security events within scope |
| `audit.dsar:process` | S | Process data subject requests |
| `audit.retention_policy:edit` | S | Set retention within platform bounds (09 PV-6) |
| `audit.consent_record:read` | | Read consent records |
| `platform.feature_flag:edit` (R) | S | Change a feature flag |
| `platform.setting:edit` | S | Change platform settings |
| `platform.job:run` | S | Run or cancel platform jobs |
| `platform.incident_tool:use` | S | Use incident tooling (circuit breakers, kill switches) |
| `platform.tenant_data:read` | S | Break-glass read of tenant data (ABAC-21) |
| `platform.break_glass:approve` | S | Approve another person's break-glass request |

---

## 4. Matrices per application

### 4.1 Learner App

One role, two account types. Personal accounts act in the consumer organisation or in organisations they joined; managed accounts act only in their organisation.

| Capability | Permission | Learner (personal) | Learner (managed) | Tier / licence |
| --- | --- | --- | --- | --- |
| View own dashboard, progress, mastery | `learning.progress:read` (own via `/me`) | 🔶 | 🔶 | Free / seat |
| Edit own profile and preferences | `identity.profile:edit` | 🔶 | 🔶 (name and email from IdP, 09 AU-23) | — |
| Browse catalogue | `learning.catalogue:read` | ✅ | ✅ (tenant's licensed catalogue) | Free / seat |
| Self-enrol | `learning.enrolment:create` | 🔶 | 🔶 if organisation policy allows | Free / seat |
| Study published lessons | `learning.lesson:study` | 🔶 (ABAC-05) | 🔶 (ABAC-05, pinned release) | Free / seat |
| Practice: quizzes, flashcards, challenges | `learning.practice:use` | 🔶 | 🔶 | Free |
| Coding lab | `learning.practice:use` | 🔶 | 🔶 | Free (quota) / Pro / seat |
| Tutor chat | `tutor.conversation:use` | 🔶 | 🔶 | Free (quota) / seat |
| Receive worked solutions | `tutor.solution:disclose` | 🔶 (denied in integrity mode, ABAC-07) | 🔶 (ABAC-07) | Free |
| Choose persona | `tutor.persona:select` | 🔶 | 🔶 within organisation options | Free |
| Adjust five dimensions | `personalisation.dimension:edit` | 🔶 | 🔶 within locks | Free |
| Upload research documents | `retrieval.document:upload` | 🔶 | 🔶 if licence includes it | Research / seat |
| Submit assignments | `assessment.submission:submit` | 🔶 (ABAC-06) | 🔶 (ABAC-06) | — |
| View own released grades and feedback | `assessment.grade:read` | 🔶 (ABAC-17) | 🔶 (ABAC-17) | — |
| Appeal a grade | `assessment.grade:appeal` | 🔶 | 🔶 | — |
| View leaderboards | `gamification.leaderboard:read` | ✅ (ABAC-28) | ✅ (ABAC-28; pseudonym default) | Free |
| Opt out of boards, set handle | `gamification.visibility:edit` | 🔶 | 🔶 within organisation policy | Free |
| Message cohort staff | `messaging.message:send` | 🔶 (own cohorts' staff) | 🔶 (own cohorts' staff) | — |
| Notification preferences | `notification.preference:edit` | 🔶 | 🔶 | — |
| Manage own subscription | `commerce.subscription:manage` | 🔶 | ❌ (licence) | — |
| Export learning passport | `learning.passport:export` | 🔶 | 🔶 if policy allows (ABAC-27) | — |
| Export or delete own account | `/me` self-service | 🔶 | ❌ (routed to the organisation, 09 PV-5) | — |
| Join another organisation | `/me` with invite or code | 🔶 with consent (ABAC-13) | ❌ | — |

### 4.2 Instructor App

`department_admin` holds Institution App powers (§4.3). The column below shows the classroom permissions the role holds through `/orgs/{org_id}`; the launcher opens the Instructor App for a `department_admin` only if they also hold a teaching role.

| Capability | Permission | `teaching_assistant` | `instructor` | `lead_instructor` | `department_admin` |
| --- | --- | --- | --- | --- | --- |
| View cohorts, members, schedules | `classroom.cohort:read` | 👥 | 👥 | 👥 🌳 | 🌳 |
| Create cohorts | `classroom.cohort:create` | ❌ | ❌ | 🌳 | 🌳 |
| Edit and archive cohorts | `classroom.cohort:edit`, `classroom.cohort:archive` | ❌ | 👥 (edit only) | 👥 🌳 | 🌳 |
| Add or remove learners | `classroom.cohort_member:add`, `:remove` | ❌ | 👥 | 👥 🌳 | 🌳 |
| Bulk import learners | `classroom.cohort_member:import` | ❌ | 👥 (ABAC-12 seats) | 👥 🌳 | 🌳 |
| Invite learners | `tenancy.membership:invite` | ❌ | 👥 | 👥 🌳 | 🌳 |
| Create managed learner accounts | `identity.account:create` | ❌ | 👥 (ABAC-19) | 👥 🌳 (ABAC-19) | 🌳 |
| Assign instructors and TAs | `classroom.cohort_staff:assign` | ❌ | ❌ | 👥 🌳 | 🌳 |
| Edit and schedule cohort plan | `classroom.cohort_plan:edit`, `:schedule` | ❌ | 👥 | 👥 🌳 | ❌ |
| Customise release (overlay) | `content.overlay:edit` | ❌ | 👥 | 👥 🌳 | ❌ |
| Lock or bound dimensions | `personalisation.dimension_lock:edit` | ❌ | 👥 | 👥 🌳 | ❌ |
| View assessments, rubrics, and assignments (including secure items, ABAC-22) | `assessment.assessment:read` | 👥 | 👥 🌳 | 👥 🌳 | 🌳 |
| Create and edit assessments and rubrics | `assessment.assessment:create`, `:edit`, `assessment.rubric:edit` | ❌ | 👥 🌳 | 👥 🌳 | ❌ |
| Publish assignments | `assessment.assignment:publish`, `:edit` | ❌ | 👥 | 👥 🌳 | ❌ |
| Set integrity mode | `assessment.integrity_mode:set` | ❌ | 👥 | 👥 🌳 | ❌ |
| Grant accommodations | `assessment.accommodation:edit` | ❌ | 👥 | 👥 🌳 | 🌳 |
| Read submissions | `assessment.submission:read` | 👥 | 👥 | 👥 🌳 | ❌ |
| Request AI marking | `assessment.ai_marking:request` | 👥 | 👥 | 👥 🌳 | ❌ |
| Mark, accept or edit AI proposals | `assessment.submission:mark` | 👥 | 👥 | 👥 🌳 | ❌ |
| Override a grade | `assessment.grade:override` | ❌ | 👥🔐 (🤝 when ABAC-16 applies) | 👥🌳🔐 | ❌ |
| Approve another's override | `assessment.grade_override:approve` | ❌ | ❌ | 👥🌳🔐 (not own, SoD-2) | ❌ |
| Release grades | `assessment.grade:release` | ❌ (unless delegated, AZ-21) | 👥 | 👥 🌳 | ❌ |
| Decide appeals | `assessment.appeal:decide` | ❌ | 👥 (SoD-9) | 👥 🌳 | ❌ |
| Read gradebook | `assessment.grade:read` | 👥 | 👥 | 👥 🌳 | 🌳 |
| Export gradebook | `assessment.gradebook:export` | ❌ | 👥🔐 | 👥🌳🔐 | 🌳🔐 |
| Export tables with identity fields (03 INS-045) | `reporting.export:create` | ❌ | 👥🔐 | 👥🌳🔐 | 🌳🔐 |
| Record and read attendance | `classroom.attendance:record`, `:read` | 👥 | 👥 | 👥 🌳 | 🌳 (read) |
| Live sessions | `classroom.live_session:edit` | ❌ | 👥 | 👥 🌳 | ❌ |
| Risk signals and interventions | `classroom.risk_signal:read`, `classroom.intervention:create` | 👥 (read) | 👥 | 👥 🌳 | 🌳 (read) |
| Learner progress and learner model | `learning.progress:read`, `personalisation.learner_model:read` | 👥 (ABAC-13) | 👥 (ABAC-13) | 👥 🌳 (ABAC-13) | 📊 |
| Message learners | `messaging.message:send` | 👥 | 👥 | 👥 🌳 | 🌳 |
| Announcements | `messaging.announcement:create` | ❌ | 👥 | 👥 🌳 | 🌳 |
| Moderate discussions | `messaging.discussion:moderate` | 👥 | 👥 | 👥 🌳 | 🌳 |
| Configure cohort leaderboard, competitions | `gamification.leaderboard:configure`, `gamification.competition:create` | ❌ | 👥 | 👥 🌳 | 🌳 |
| Cohort reports | `reporting.report:read` | 👥 | 👥 | 👥 🌳 | 🌳 |
| Cohort analytics | `analytics.dashboard:read` | 👥 | 👥 | 👥 🌳 | 🌳 |
| Search people | `search.person:query` | 👥 | 👥 | 👥 🌳 | 🌳 |

### 4.3 Institution App

| Capability | Permission | `org_owner` | `org_admin` | `campus_admin` | `department_admin` | `org_billing_manager` | `org_report_viewer` | `org_compliance_officer` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| View organisation | `tenancy.organisation:read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit organisation details | `tenancy.organisation:edit` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Delete organisation | `tenancy.organisation:delete` | 🔐🤝 (second `org_owner` if more than one) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Org structure (campuses, departments) | `tenancy.org_unit:edit` | ✅ | ✅ | 🌳 | 🌳 (sub-department) | ❌ | ❌ | ❌ |
| Members: list | `tenancy.membership:read` | ✅ | ✅ | 🌳 | 🌳 | 📊 (seat counts) | ❌ | ✅ |
| Members: invite, import | `tenancy.membership:invite`, `:import` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ❌ | ❌ |
| Members: suspend, end | `tenancy.membership:end` | 🔐 | 🔐 | 🌳🔐 | ❌ | ❌ | ❌ | ❌ |
| Managed accounts: create, suspend | `identity.account:create`, `:suspend` | ✅ | ✅ | 🌳 | 🌳 (create) | ❌ | ❌ | ❌ |
| Revoke sessions, reset MFA (non-SSO managed accounts) | `identity.session:revoke`, `identity.mfa:reset` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Enrolment codes | `tenancy.enrolment_code:create` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ❌ | ❌ |
| Role assignments: view | `authz.role_assignment:read` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ❌ | ✅ |
| Role assignments: grant, revoke (§8) | `authz.role_assignment:grant`, `:revoke` | 🔐 | 🔐 | 🌳🔐 | 🌳🔐 | ❌ | ❌ | ❌ |
| Organisation policies and policy flags | `tenancy.org_policy:edit`, `authz.policy:edit` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| SSO connection | `tenancy.sso_connection:configure` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Domain verification | `tenancy.domain:verify` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Custom domain (R4) | `tenancy.custom_domain:configure` | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Branding | `tenancy.branding:edit` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SCIM, OneRoster, LTI (R4) | `integration.scim_client:configure`, `integration.oneroster_sync:configure`, `integration.lti_platform:configure` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Webhooks, xAPI export | `integration.webhook_endpoint:configure`, `integration.xapi_export:configure` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cohorts: create, oversee | `classroom.cohort:create`, `classroom.cohort:read` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ❌ | ❌ |
| Assign cohort staff | `classroom.cohort_staff:assign` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ❌ | ❌ |
| Licences and seats: view | `commerce.licence:read` | ✅ | ✅ | 📊 | 📊 | ✅ | ❌ | ❌ |
| Seats: assign | `commerce.seat:assign` | ✅ | ✅ | 🌳 | 🌳 | ✅ | ❌ | ❌ |
| Invoices | `commerce.invoice:read` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Payment method | `commerce.payment_method:edit` | 🔐 | ❌ | ❌ | ❌ | 🔐 | ❌ | ❌ |
| AI usage and cost | `ai.usage:read` | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Dashboards | `analytics.dashboard:read` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ✅ (scope held) | ❌ |
| Reports: run, define, schedule | `reporting.report:read`, `:create`, `:schedule` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ✅ (read, schedule) | ✅ (read) |
| Learner-level export | `reporting.export:create` | 🔐 | 🔐 | 🌳🔐 | 🌳🔐 | ❌ | ❌ | 🔐 |
| Learner progress (individual) | `learning.progress:read` | ✅ (ABAC-13) | ✅ (ABAC-13) | 🌳 (ABAC-13) | 🌳 (ABAC-13) | ❌ | 📊 | ❌ |
| Gradebooks (read) | `assessment.grade:read` | ✅ | ✅ | 🌳 | 🌳 | ❌ | 📊 | ❌ |
| Institution leaderboards | `gamification.leaderboard:configure` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ❌ | ❌ |
| Announcements to org units | `messaging.announcement:create` | ✅ | ✅ | 🌳 | 🌳 | ❌ | ❌ | ❌ |
| Notification template overrides | `notification.template:edit` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Org workspace content roles (licence) | `content.*` via workspace roles | see §8 | see §8 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Audit log: read | `audit.log:read` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audit log: export | `audit.log:export` | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ | 🔐 |
| Data access log (incl. AI Mentor staff access) | `audit.data_access_log:read` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Security events (R4) | `audit.security_event:read` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| DSAR queue | `audit.dsar:process` | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ | 🔐 |
| Retention policy | `audit.retention_policy:edit` | 🔐🤝 (with compliance officer) | ❌ | ❌ | ❌ | ❌ | ❌ | 🔐 |
| Consent records | `audit.consent_record:read` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Compliance reports | `reporting.compliance_report:read` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Tutor transcripts of a managed learner | `tutor.conversation:read` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 🎫 (ABAC-26) |
| Custom roles (R4) | `authz.custom_role:edit` | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 4.4 Admin App

All rows require `azp` = Admin App (ABAC-08) and a second factor at sign-in. Reads of tenant data outside the platform's own records need break-glass (ABAC-21).

| Capability | Permission | `platform_admin` | `platform_operator` | `ai_admin` | `security_auditor` | `support_agent` | `finance_admin` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| List and view accounts | `identity.account:read` | ✅ | ❌ | ❌ | 📊 | 🎫 | 🎫 (billing fields) |
| Suspend an account | `identity.account:suspend` | 🔐 | ❌ | ❌ | ❌ | 🎫🔐 | ❌ |
| Export or erase on a person's behalf | `identity.account:export`, `:erase` | 🎫🔐 | ❌ | ❌ | ❌ | 🎫🔐 | ❌ |
| Revoke sessions, reset MFA | `identity.session:revoke`, `identity.mfa:reset` | 🎫🔐 | ❌ | ❌ | ❌ | 🎫🔐 (revoke only) | ❌ |
| Platform role assignments | `authz.role_assignment:grant`, `:revoke` | 🔐 (not self) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Role assignments and decision log | `authz.role_assignment:read`, `authz.decision_log:read` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Create organisations | `tenancy.organisation:create` | 🔐 | ❌ | ❌ | ❌ | ❌ | 🔐 |
| View organisations | `tenancy.organisation:read` | ✅ | ✅ | ❌ | ✅ | 🎫 | ✅ |
| Edit organisation kind and settings | `tenancy.organisation:edit` | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Suspend organisations | `tenancy.organisation:suspend` | 🔐🤝 | ❌ | ❌ | ❌ | ❌ | 🔐🤝 (non-payment) |
| Provision org workspace | `content.workspace:create` | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Licences | `commerce.licence:read`, `commerce.licence:edit` | ✅ (read) | ❌ | ❌ | ❌ | 🎫 (read) | 🔐 |
| Consumer plans | `commerce.plan:edit` | ❌ | ❌ | ❌ | ❌ | ❌ | 🔐 |
| Consumer subscriptions | `commerce.subscription:manage` | ✅ (read) | ❌ | ❌ | ❌ | 🎫 (read) | 🔐 |
| Invoices, refunds | `commerce.invoice:read`, `commerce.refund:issue` | ✅ (read) | ❌ | ❌ | ❌ | 🎫 (read) | 🔐 (🤝 above threshold) |
| Feature flags | `platform.feature_flag:edit` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ |
| Platform settings | `platform.setting:edit` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ |
| Jobs | `platform.job:run` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ |
| Incident tooling | `platform.incident_tool:use` | 🔐 | 🔐 | 🔐 (AI circuit breaker) | ❌ | ❌ | ❌ |
| Break-glass read of tenant data | `platform.tenant_data:read` | 🎫🔐 | 🎫🔐 (configuration only) | ❌ | ❌ | 🎫🔐 (account and membership only) | ❌ |
| Approve break-glass | `platform.break_glass:approve` | 🔐 (not own, SoD-6) | ❌ | ❌ | 🔐 (not own) | ❌ | ❌ |
| Model registry, routing | `ai.model:register`, `ai.model_route:edit` | ❌ | ❌ | 🔐 | ❌ | ❌ | ❌ |
| Prompt and persona releases | `ai.prompt_release:publish`, `tutor.persona:configure` | ❌ | ❌ | 🔐 (🤝 for marking and safety, SoD-7) | ❌ | ❌ | ❌ |
| Guardrails | `ai.guardrail:edit` | ❌ | ❌ | 🔐 | ❌ | ❌ | ❌ |
| Evaluations | `ai.evaluation:run` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| AI usage and cost | `ai.usage:read` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Moderation queue | `tutor.flagged_message:review` | ✅ | ❌ | ✅ | ❌ | 🎫 | ❌ |
| Leaderboard fraud holds | `gamification.entry:hold` | ✅ | ❌ | ❌ | ❌ | 🎫 | ❌ |
| XP corrections | `gamification.xp:adjust` | 🎫🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Platform-wide notices | `notification.broadcast:send` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ |
| Platform templates | `notification.template:edit` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Search and index rebuilds | `search.index:rebuild`, `retrieval.index:rebuild` | 🔐 | 🔐 | ❌ | ❌ | ❌ | ❌ |
| Platform analytics and benchmarks | `analytics.dashboard:read`, `analytics.benchmark:read` | 📊 | 📊 | 📊 | ❌ | ❌ | 📊 |
| Audit log (all tenants) | `audit.log:read` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Audit export | `audit.log:export` | 🔐 | ❌ | ❌ | 🔐 | ❌ | ❌ |
| Data access log, security events | `audit.data_access_log:read`, `audit.security_event:read` | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| DSARs (personal accounts) | `audit.dsar:process` | 🎫🔐 | ❌ | ❌ | ❌ | 🎫🔐 | ❌ |
| UI message catalogues | `i18n.message_catalogue:edit` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Partner API clients (R5) | `integration.api_client:configure` | 🔐 | ❌ | ❌ | ❌ | ❌ | ❌ |

### 4.5 Content Studio

Columns are workspace roles; a cell applies in the workspace where the role is held. `platform_admin` reads every workspace from the Content Studio (README) and writes nothing unless they also hold a workspace role, except an emergency takedown. v1 admins are migrated with `content_publisher` and `knowledge_steward` in `master` for that reason (§10).

| Capability | Permission | `content_author` | `content_reviewer` | `content_publisher` | `knowledge_steward` | `localisation_editor` | `platform_admin` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Read items in all states | `content.item:read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (read) |
| Create drafts | `content.item:create` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Edit drafts | `content.item:edit` | ✅ | ✅ (becomes last editor, SoD-1) | ❌ | ❌ | ❌ | ❌ |
| AI-generate drafts | `content.item:generate` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit for review | `content.item:submit` | ✅ | ✅ | ❌ | ❌ | ✅ (translations) | ❌ |
| Approve or request changes | `content.item:review` | ❌ | ✅ (ABAC-04) | ❌ | ❌ | ❌ | ❌ |
| Publish course or path release | `content.course:publish`, `content.path:publish` | ❌ | ❌ | 🔐 (ABAC-05 checks passed) | ❌ | ❌ | ❌ |
| Schedule, archive, restore | `content.release:schedule`, `:archive`, `:restore` | ❌ | ❌ | 🔐 | ❌ | ❌ | ❌ |
| Upload and edit knowledge assets | `knowledge.asset:upload`, `:edit` | ✅ | ✅ (edit) | ❌ | ✅ (metadata) | ❌ | ❌ |
| Read knowledge assets | `knowledge.asset:read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (read) |
| Take down an asset or a published item | `knowledge.asset:take_down`, `content.item:take_down` | ❌ | ❌ | 🎫🔐 (🤝 `platform_admin` in `master`, SoD-11) | ❌ | ❌ | 🎫🔐 (emergency) |
| Taxonomy and vocabularies | `knowledge.taxonomy:edit` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Concepts and concept graph | `knowledge.concept:edit`, `knowledge.concept_relation:edit` | ❌ (propose via draft) | ❌ | ❌ | ✅ (🔐 in `master`) | ❌ | ❌ |
| Metadata schema | `knowledge.metadata_schema:edit` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Translate | `content.translation:edit` | ❌ | ❌ | ❌ | ❌ | ✅ (ABAC-24) | ❌ |
| Approve translations | `content.translation:approve` | ❌ | ✅ (ABAC-24, not own) | ❌ | ❌ | ✅ (ABAC-24, not own) | ❌ |
| Ingestion jobs and quarantine | `retrieval.ingestion_job:read`, `retrieval.chunk:quarantine` | ✅ (read) | ✅ | ✅ | ✅ | ❌ | ✅ (read) |
| Derived courses (org workspace) | `content.derived_course:create` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Assessment item bank (master), read | `assessment.assessment:read` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Assessment item bank (master) | `assessment.assessment:create`, `:edit`, `assessment.rubric:edit` | ✅ | ✅ (edit) | ❌ | ❌ | ❌ | ❌ |
| Badge definitions | `gamification.badge:define` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 5. Cross-app data visibility

What each role can see of a person's data, per ADR 0021. "Assigned" means concepts in curricula the organisation assigned, while the membership is active, within consent (ABAC-13).

| Viewer | Learning record, personal account | Learning record, managed account | Academic record | Tutor transcripts | Profile and contact |
| --- | --- | --- | --- | --- | --- |
| The learner | 🔶 all | 🔶 all | 🔶 own, released grades only (ABAC-17) | 🔶 | 🔶 |
| `teaching_assistant` | 👥 assigned, consented | 👥 | 👥 (no grades before release unless marking) | ❌ | 👥 name, handle |
| `instructor`, `lead_instructor` | 👥 / 🌳 assigned, consented | 👥 / 🌳 | 👥 / 🌳 | ❌ (topic summaries 📊) | 👥 / 🌳 name, email |
| `department_admin`, `campus_admin` | 🌳 assigned, consented | 🌳 | 🌳 | ❌ | 🌳 |
| `org_admin`, `org_owner` | ✅ assigned, consented | ✅ | ✅ | ❌ | ✅ |
| `org_report_viewer` | 📊 | 📊 | 📊 | ❌ | ❌ |
| `org_compliance_officer` | Consent records only | ✅ for DSAR and audit | ✅ for DSAR and audit | 🎫 if `tutor.transcript_access` (ABAC-26) | ✅ |
| `org_billing_manager` | ❌ | ❌ | ❌ | ❌ | Seat holder name only |
| Other organisations | ❌ | ❌ | ❌ | ❌ | ❌ |
| `support_agent` | 🎫 metadata only | 🎫 metadata only | ❌ | ❌ | 🎫 |
| `platform_admin` | 🎫 break-glass | 🎫 break-glass | 🎫 break-glass 🤝 | 🎫 break-glass 🤝 | ✅ (platform records) |
| `security_auditor` | ❌ (audit records only) | ❌ | ❌ | ❌ | Internal ids only |
| `ai_admin` | 📊 (evaluation sets are de-identified) | 📊 | 📊 | ❌ (flagged excerpts via moderation queue only) | ❌ |
| Content roles | ❌ | ❌ | ❌ | ❌ | Author names of content only |
| Other learners | Leaderboard entry (ABAC-28) | Leaderboard entry, pseudonym by default | ❌ | ❌ | Handle in shared cohorts |

After a personal account leaves an organisation or withdraws consent, the organisation keeps the academic record it issued and loses the learning record view. After a managed account's membership ends, the organisation keeps both under its retention policy.

---

## 6. ABAC condition catalogue

| ID | Condition | Attributes | Where applied |
| --- | --- | --- | --- |
| ABAC-01 | Same tenant: resource `tenant_id` equals the active tenant; active tenant has an `active` membership | Resource `tenant_id`; subject memberships; context active tenant | Every tenant-scoped permission |
| ABAC-02 | Org-unit subtree: `resource_path <@ scope_path` | Resource org-unit path; assignment scope path | Every org-unit-scoped permission |
| ABAC-03 | Cohort staff relationship: subject listed in `classroom.cohort_staff` for the resource's cohort | Relationship | 👥 cells; TA permissions always |
| ABAC-04 | Two-person rule: reviewer is not the author and not the last material editor; exception only in `org` workspaces with fewer than three eligible reviewers, logged | Relationship (author of, last editor of); workspace kind; org policy | `content.item:review`, `content.translation:approve` |
| ABAC-05 | Content state: learners and the tutor see only `published` items, from the release pinned to their cohort where one exists | Resource state, release pin | `learning.lesson:study`, `learning.catalogue:read`, retrieval, `content.*:publish` precondition (release checks passed) |
| ABAC-06 | Assessment window: `open_at ≤ now < close_at`, extended by the learner's accommodation; attempts remaining | Resource window; accommodation; context time | `assessment.submission:submit` |
| ABAC-07 | Integrity mode (explicit deny): while the learner has an open assignment in integrity mode, deny solution disclosure for its concepts and items, and deny `exam_coach` | Context integrity mode; resource concepts | `tutor.solution:disclose`, `tutor.conversation:use` (mode `exam_coach`) |
| ABAC-08 | App audience: `azp` is the Admin App for `platform.*` and every permission held at platform scope; Content Studio for `content.*` and `knowledge.*` writes; Instructor or Institution App for `/orgs` | Subject `azp` | All, by route root (09 AU-14) |
| ABAC-09 | MFA freshness: second factor verified within 15 minutes | Subject `fva` | Sensitive permissions (§3, S) and 🔐 cells |
| ABAC-10 | MFA present at sign-in, per app rule or organisation policy | Subject `fva`; org policy | Admin App, Content Studio (`master`), Institution App (`org_owner`, `org_admin`) |
| ABAC-11 | Ticket reference: request carries a ticket or case id that exists and is open | Context reason | `support_agent` reads; 🎫 cells |
| ABAC-12 | Licence seat: the learner holds an assigned seat for licensed features; imports and invitations do not exceed seats plus overage | Subject seat; licence | Learning features in licensed tenants; `classroom.cohort_member:import`; `tenancy.membership:invite` |
| ABAC-13 | Consent scope: for personal accounts, the organisation sees learning record data only for assigned curricula, while membership is active, within `assigned_progress` consent | Subject (viewer) tenant; resource account type; consent record | `learning.progress:read`, `personalisation.learner_model:read`, reports and dashboards |
| ABAC-14 | Membership active: suspended or ended memberships open no tenant context | Membership status | Every tenant-scoped permission |
| ABAC-15 | Owner only: the subject owns the record | Resource owner | 🔶 cells |
| ABAC-16 | Override approval: when org policy `grades.override_approval` is `lead_instructor`, an override is pending until a `lead_instructor` other than the overrider approves | Org policy; relationship | `assessment.grade:override`, `assessment.grade_override:approve` |
| ABAC-17 | Released grades only: learners see grades after release; proposed grades are never visible to learners | Resource grade state | `assessment.grade:read` for learners |
| ABAC-18 | Frozen assessment (explicit deny): after the first submission, items and keys cannot change; after release, grades change only by override | Resource state | `assessment.assessment:edit`, `assessment.assignment:edit` |
| ABAC-19 | Instructor-created accounts: org policy `members.instructor_can_create` is on | Org policy | `identity.account:create` for teaching roles |
| ABAC-20 | IP allowlist: request IP is within the organisation's allowlist when set (R4) | Context IP; org policy | Institution App; optionally Instructor App |
| ABAC-21 | Break-glass session: a valid `break_glass_id` for this tenant and record class, unexpired, approved where required | Context break-glass | `platform.tenant_data:read` and every platform read of tenant data |
| ABAC-22 | Secure item: item classification `secure` hides it from search, retrieval, and anyone without `assessment.assessment:read` at scope | Resource classification | Item bank, search, retrieval |
| ABAC-23 | Subscription tier: consumer tier includes the feature and quota remains | Subject tier; quota | Learner App features (v1 tier column) |
| ABAC-24 | Assigned locale: editor or reviewer is assigned the item's target locale; graded items used in a locale only when `translation_status = approved` | Subject locales; resource locale | `content.translation:*`; assessment delivery |
| ABAC-25 | Not learner and staff in the same cohort | Relationship | Grant of cohort roles; `assessment.submission:mark` |
| ABAC-26 | Transcript access: org policy `tutor.transcript_access` on, learners notified, reason recorded, managed account only | Org policy; resource account type; context reason | `tutor.conversation:read` by organisation roles |
| ABAC-27 | Passport policy: org policy `records.passport_export` allows managed accounts to export | Org policy | `learning.passport:export` for managed accounts |
| ABAC-28 | Leaderboard visibility: board defaults of 09 §11.3; viewer sees boards for their tenant, cohorts, friends, and public boards | Resource board scope; subject memberships; learner visibility settings; org opt-out | `gamification.leaderboard:read` |
| ABAC-29 | Export volume: exports above 1,000 learner records or the tenant's p99 require a fresh step-up and notify `org_owner` | Context volume | `reporting.export:create`, `assessment.gradebook:export`, `audit.log:export` |
| ABAC-30 | Delegation ceiling: §8 table lists the role for the grantor's role, and the grantor holds every governance permission the role contains at a containing scope | Subject assignments; target role | `authz.role_assignment:grant`, `classroom.cohort_staff:assign` |

---

## 7. Separation of duties

| ID | Rule | Enforced by |
| --- | --- | --- |
| SoD-1 | An item is approved by someone other than its author and its last material editor | ABAC-04 |
| SoD-2 | When override approval is required, the approver is not the overrider | ABAC-16 |
| SoD-3 | `security_auditor` cannot be held together with `platform_admin`, `platform_operator`, or `ai_admin` | Grant-time check |
| SoD-4 | Nobody grants or revokes their own role assignments, at any scope | Grant-time check (carries v1 self-change guard) |
| SoD-5 | A person cannot be `learner` and staff (`teaching_assistant`, `instructor`, `lead_instructor`) in the same cohort | ABAC-25 |
| SoD-6 | A break-glass requester cannot approve their own request | ABAC-21 |
| SoD-7 | Prompt releases for AI marking, safety, and personas need a second `ai_admin` (or `platform_admin`) to approve after the evaluation gate | `ai.prompt_release:publish` workflow |
| SoD-8 | Refunds above the configured threshold, and licence changes above the configured value, need a second `finance_admin` or a `platform_admin` | `commerce.refund:issue`, `commerce.licence:edit` workflow |
| SoD-9 | An appeal is decided by someone other than the original marker when the cohort has more than one marker | `assessment.appeal:decide` |
| SoD-10 | Deleting an organisation with more than one `org_owner` needs a second `org_owner`; retention changes need both an `org_owner` and the `org_compliance_officer` | 🤝 cells in §4.3 |
| SoD-11 | A takedown in `master` by a `content_publisher` takes effect only after a `platform_admin` approves; a `platform_admin` may take down alone in an emergency, with a recorded reason | `content.item:take_down`, `knowledge.asset:take_down` workflow |

---

## 8. Delegation rules

Grants are checked against this table (seed data `authz.delegations`), then against the governance ceiling (ABAC-30), then SoD-3, SoD-4, and SoD-5. A grant's scope must be inside the grantor's scope. Platform roles are granted only through `/platform` from the Admin App. Organisation roles cannot be granted from the platform context except the first `org_owner` at creation, and owner recovery with a ticket and contract evidence (🎫).

| Grantor | May grant | At scopes |
| --- | --- | --- |
| `platform_admin` | All platform roles; `content_author`, `content_reviewer`, `content_publisher`, `knowledge_steward`, `localisation_editor` | Platform; `master` workspace |
| `platform_admin` (onboarding, recovery 🎫) | `org_owner` | A new or ownerless organisation |
| `org_owner` | `org_owner`, `org_admin`, `org_billing_manager`, `org_compliance_officer`, `org_report_viewer`, `campus_admin`, `department_admin`, `lead_instructor`, `instructor`, `teaching_assistant`, `learner`; workspace roles | Own organisation and below; own `org` workspace |
| `org_admin` | `org_report_viewer`, `campus_admin`, `department_admin`, `lead_instructor`, `instructor`, `teaching_assistant`, `learner`; `content_author`, `content_reviewer`, `localisation_editor` | Own organisation and below; own `org` workspace |
| `campus_admin` | `department_admin`, `org_report_viewer`, `lead_instructor`, `instructor`, `teaching_assistant`, `learner` | Own campus and below |
| `department_admin` | `org_report_viewer`, `lead_instructor`, `instructor`, `teaching_assistant`, `learner` | Own department and below |
| `lead_instructor` | `instructor`, `teaching_assistant` (via `classroom.cohort_staff:assign`), `learner` | Cohorts within own scope |
| `instructor` | `learner` (via cohort membership) | Own cohorts |
| SCIM, OneRoster, JIT, LTI | `learner`; `teaching_assistant` and `instructor` through org-configured mappings only (09 AU-20, SSO-5, SSO-10) | Organisation or mapped cohort |
| Self | `learner` in the consumer organisation; `learner` in an organisation through an invitation or enrolment code | Consumer organisation; invited organisation |

Additional rules:

1. `org_owner` cannot assign platform roles, and no organisation role can (the table has no such row).
2. A time-boxed assignment (`expires_at`) may be granted by anyone allowed to grant the role; it SHOULD be used for TA delegation of `assessment.grade:release` (09 AZ-21).
3. Revocation follows the same table. The last `org_owner` and last `platform_admin` cannot be revoked (09 AZ-17).
4. Every grant and revoke publishes `authz.role_assignment.granted` or `authz.role_assignment.revoked` and invalidates the cache (09 AZ-18).

---

## 9. Default role templates and custom roles

**Templates.** The 22 human roles are platform-defined templates. Their permission sets are seed data, versioned with the code, and identical in every organisation. Organisations cannot edit them.

**Starter assignments by organisation kind** (a suggestion the Institution App offers at onboarding; nothing is granted automatically except the first `org_owner`):

| Kind | Suggested structure and roles |
| --- | --- |
| `university`, `college` | Campuses and faculties as departments; `department_admin` per department; `lead_instructor` per course; `org_compliance_officer` required |
| `school` | Departments only; `department_admin`; age attestation (09 PV-8) |
| `enterprise`, `government` | Departments as teams; `org_report_viewer` at department for managers; cohorts per programme |
| `bootcamp` | Cohorts directly under the organisation; `lead_instructor` per cohort |
| `publisher` | `org` workspace with content roles; few or no learners |
| `consumer` | Platform-managed; no organisation roles |

**Custom roles (R4, 09 AZ-20).** An `org_owner` may define a custom role as a named subset of permissions with allowed scope types, subject to:

1. No permission in contexts `platform` or `ai`, and none of `authz.custom_role:edit`, `tenancy.organisation:delete`, `tenancy.custom_domain:configure`, `commerce.payment_method:edit`.
2. No permission the defining `org_owner` does not hold.
3. SoD rules apply to custom roles by permission: a custom role holding both `assessment.grade:override` and `assessment.grade_override:approve` is allowed, but ABAC-16 still prevents approving one's own override.
4. Custom roles are tenant-scoped rows in `authz.roles` with `tenant_id` set, appear in the organisation's matrix export, and are covered by the BFLA suite through generated tests.
5. Changes to a custom role are audited and take effect within the cache window (60 seconds).

---

## 10. Migration and test requirements

### 10.1 v1 role mapping (README, ADR 0016)

| v1 `users.role` | v2 assignments |
| --- | --- |
| `student` | `learner` in the consumer organisation |
| `instructor` | `content_author` in the `master` workspace, plus `learner` in the consumer organisation |
| `admin` | `platform_admin`, plus `content_publisher` and `knowledge_steward` in `master`, plus `learner` in the consumer organisation |
| v1 proposed `content_reviewer` | `content_reviewer` in `master` |
| v1 proposed `support` | `support_agent` |

Notes:

- v1 `instructor` users today pass the staff gate on `/api/v1/admin/analytics`. After migration they hold no Instructor App role (they were authors, not classroom teachers), so aggregated platform analytics move to `platform_admin`. Any v1 instructor who needs analytics is granted an appropriate role explicitly.
- v1 `admin` users did not need a separate reviewer role to approve, because the four-eyes rule was applied between admins. After migration, approving requires `content_reviewer`. Grant it in `master` to the v1 admins who reviewed content; otherwise the workflow stalls.
- Migration sequence: expand (create `authz` tables and seed), backfill (assignments from `users.role`), switch (routers on `require()`, `is_allowed` as shim), contract (drop `users.role`, replace RLS role-name policies, 09 AZ-22).

### 10.2 v1 route mapping

| v1 route | v1 check | v2 permission |
| --- | --- | --- |
| `GET /admin/users` | `admin` | `identity.account:read` (platform) |
| `PATCH /admin/users/{id}` (role) | `admin`, last-admin and self-change guards | `authz.role_assignment:grant` / `:revoke` (platform), SoD-4, AZ-17 |
| `GET /admin/analytics` | `instructor` or `admin` | `analytics.dashboard:read` (platform) |
| Asset create, edit, transition | `instructor` or `admin`, four-eyes | `knowledge.asset:upload`, `knowledge.asset:edit`, `content.item:review`, `content.course:publish` (workspace `master`) |
| Configuration, providers | `admin` | `platform.setting:edit`, `ai.model_route:edit` |
| Audit log | `admin` | `audit.log:read` (platform) |
| Learner routes (`/me`, chat, quizzes, cards, lab, research) | authenticated, owner-scoped | `identity.profile:edit`, `tutor.conversation:use`, `learning.practice:use`, `retrieval.document:upload`, each with ABAC-15 |

### 10.3 Matrix as code

| Artefact | Location (target) | Rule |
| --- | --- | --- |
| Role, permission, and delegation seed | `backend/app/domain/authz/seed/` (`roles.yaml`, `permissions.yaml`, `delegations.yaml`) | Single source of truth. Migrations load it into `authz.roles`, `authz.permissions`, `authz.role_permissions`, `authz.delegations` |
| Matrix fixtures | `backend/tests/fixtures/authz_matrix.json`, generated from the seed and the per-app capability rows | Drive the BFLA suite |
| This document's matrices | Rendered by `python -m app.cli authz render-matrix` | CI fails if the rendered tables differ from this file |
| App route guards | Shared package (ADR 0014) generated from the seed | Render-only; never the enforcement point |

### 10.4 Test requirements

| ID | Test | Gate |
| --- | --- | --- |
| RT-1 | **Permission coverage**: enumerate every FastAPI route; fail if a route has no `require()` and is not on the public allow-list; fail if a permission named by a route is not in the seed | Every PR from R1 |
| RT-2 | **Catalogue integrity**: every permission matches `^[a-z_]+\.[a-z_]+:[a-z_]+$`, its context is a module from the README (with `ai` and `platform` aliases), and it appears exactly once | Every PR |
| RT-3 | **BFLA**: for every route and every role (single assignment at a representative scope), the response matches the fixture (allowed, 403, or 404) | Every PR |
| RT-4 | **BOLA per tenant**: two tenants × two principals per tenant-scoped endpoint (09 AZ-15) | Every PR |
| RT-5 | **Scope containment**: cohort, department, campus, organisation, and workspace assignments tested against sibling and parent units | Every PR from R3 |
| RT-6 | **ABAC predicates**: each ABAC-01 to ABAC-30 condition has at least one allow and one deny unit test | Every PR |
| RT-7 | **SoD and delegation**: each SoD rule and each row of §8 has a positive and a negative test, including self-grant and platform-role grant from `/orgs` | Every PR |
| RT-8 | **App audience**: each sensitive route is called with tokens from each of the five apps | Every PR |
| RT-9 | **Explicit deny precedence**: `platform_admin` cannot bypass integrity mode, frozen assessments, or suspended memberships | Every PR from R3 |
| RT-10 | **Drift**: rendered matrix equals this document | Every PR |
| RT-11 | **Decision log**: sensitive permissions always log; denies always log | Every PR |
| RT-12 | **Custom roles** (R4): forbidden permissions refused; generated BFLA cases pass | Every PR from R4 |
