# AI Mentor platform documentation (v2.0, enterprise ecosystem)

| Field | Value |
| --- | --- |
| Version | 2.0 |
| Date | 13 October 2026 |
| Status | Approved direction. Target architecture; most of it is not built yet |
| Owners | Product (CPO), Technology (CTO), Learning (CLO), Enterprise Architecture |
| Supersedes in part | The v1 documents listed in [Relationship to v1 documents](#relationship-to-v1-documents) |

AI Mentor is changing from one AI tutoring application into a learning ecosystem: five applications on one shared platform, serving many organisations. This folder is the authoritative description of that direction. The v1 documents in `docs/` stay normative for anything this folder does not change, mostly the detailed learner feature rules.

This file is the **canonical vocabulary**. Every document in this folder uses the names, identifiers, and boundaries defined here. If a document disagrees with this file, this file wins and the other document is a defect.

## Contents

1. [Document set](#document-set)
2. [Precedence and change control](#precedence-and-change-control)
3. [Relationship to v1 documents](#relationship-to-v1-documents)
4. [The five applications](#the-five-applications)
5. [Tenancy model](#tenancy-model)
6. [Accounts and learner records](#accounts-and-learner-records)
7. [Roles and scopes](#roles-and-scopes)
8. [Permissions and attributes](#permissions-and-attributes)
9. [Content model](#content-model)
10. [Teaching and assessment vocabulary](#teaching-and-assessment-vocabulary)
11. [Shared platform services](#shared-platform-services)
12. [Domain events](#domain-events)
13. [Personalisation, mentor, and language vocabulary](#personalisation-mentor-and-language-vocabulary)
14. [Releases](#releases)
15. [Identifier conventions](#identifier-conventions)
16. [Canonical data and API names](#canonical-data-and-api-names)
17. [Glossary](#glossary)

---

## Document set

Read in this order. Numbers are stable; do not renumber.

| # | Deliverable | File |
| --- | --- | --- |
| 1 | Documentation gap analysis | [00-gap-analysis.md](00-gap-analysis.md) |
| 2 | Product vision | [01-product-vision.md](01-product-vision.md) |
| 3 | Product requirements (PRD v2) | [02-prd.md](02-prd.md) |
| 4 | Software requirements (SRS v2) | [03-srs.md](03-srs.md) |
| 5 | Use cases | [04-use-cases.md](04-use-cases.md) |
| 6 | User stories | [05-user-stories.md](05-user-stories.md) |
| 7 | System architecture | [06-system-architecture.md](06-system-architecture.md) |
| 8 | Database design | [07-database-design.md](07-database-design.md) |
| 9 | API specification | [08-api-specification.md](08-api-specification.md) |
| 10 | Security model | [09-security-model.md](09-security-model.md) |
| 11 | RBAC and ABAC matrix | [10-rbac-matrix.md](10-rbac-matrix.md) |
| 12 | UX specification | [11-ux-specification.md](11-ux-specification.md) |
| 13 | Information architecture | [12-information-architecture.md](12-information-architecture.md) |
| 14 | Knowledge management architecture | [13-knowledge-management-architecture.md](13-knowledge-management-architecture.md) |
| 15 | Content Studio specification | [14-content-studio-specification.md](14-content-studio-specification.md) |
| 16 | Roadmap | [15-roadmap.md](15-roadmap.md) |
| 17 | Architecture decision records | [ADR 0013 to 0027](../adr/README.md) |

Every document in this folder opens with a **Change record** table with four rows: what changed, why, impacted systems, and implementation implications. That is how each update explains itself.

## Precedence and change control

1. This file (vocabulary and boundaries).
2. Accepted ADRs (0001–0027). A later ADR wins over an earlier one it amends.
3. Documents `00`–`15` in this folder.
4. v1 documents in `docs/`, for anything not changed by 1–3.
5. `Architecture.md`, `API.md`, `Database.md`, and `Security.md` describe the code that runs today. They change when code changes, not when this folder changes.

A change to a role, permission, scope, application boundary, event name, or release label starts here, then flows to the affected documents in the same pull request.

## Relationship to v1 documents

| v1 document | Status under v2 | Replaced or extended by |
| --- | --- | --- |
| `Requirements.md`, `Admin.md` | Retained as original product briefs. Not edited | 01, 02, 13, 14 |
| `PRD.md` | Feature specs F1–F27, metrics, and monetisation retained for the Learner App. Vision, personas, scope, and roadmap superseded | 01, 02, 15 |
| `SRS.md` | All v1 requirement IDs stay valid. Sections 2, 4, 5, and 21 superseded | 03 |
| `UseCases.md` | UC-01 to UC-38 and Epics 1–16 retained. Actors and permissions sections superseded | 04, 05 |
| `SystemArchitecture.md` | Sections 8, 11, 13–17 retained. Sections 1–5, 9, 10, 12 extended | 06, 13 |
| `database/*`, ADR 0011 | Retained as the base schema. Extended with tenancy and 14 new schemas | 07 |
| `openapi.yaml`, `API.md` | Describe live routes. Unchanged until routes ship | 08 |
| `Security-Compliance.md` | Sections 6–17 retained. Sections 4 and 5 superseded | 09, 10 |
| `DesignSpec.md` | Sections 1–7 (design system) retained for all five apps. Sections 8–17 extended | 11, 12, 14 |
| `Roadmap.md` | Describes the current build slice only | 15 |
| `Knowledge-Catalog.md` | Running Resource Catalog and Knowledge Pack. Target home is Content Studio | 13, 14 |
| `TestPlan.md` | Retained for R1. A v2 test plan is a follow-up (see 00, gap G-27) | 00 |

---

## The five applications

Users are not "roles inside one app". Each user group has its own application, with its own navigation, dashboards, permissions, and workflows, on one platform.

| App | Code name | Primary users | Purpose | Origin | Source directory (target) |
| --- | --- | --- | --- | --- | --- |
| Learner App | `learner` | Learners | Learning, assessment, engagement, competition, career progression | `learn.<domain>` (marketing site at `<domain>`) | `apps/learner` (today `frontend/`) |
| Instructor App | `instructor` | Lead instructors, instructors, teaching assistants | Teaching, learner management, assessment, intervention | `teach.<domain>` | `apps/instructor` (new) |
| Institution App | `institution` | Organisation owners and admins, campus and department admins, report viewers, compliance officers, billing managers | Organisation-level management | `org.<domain>` | `apps/institution` (new) |
| Admin App | `admin` | Platform admins, operators, AI admins, support, auditors, finance | Platform governance and operations | `admin.<domain>` | `apps/admin` (today the operations half of `admin/`) |
| Content Studio | `studio` | Content authors (SMEs, curriculum designers), reviewers, publishers, knowledge stewards, localisation editors | Knowledge management, curriculum creation, content operations, learning asset management | `studio.<domain>` | `apps/studio` (today the content half of `admin/`) |

Rules:

- **Naming.** "Studio" means Content Studio only. The learner application is the "Learner App". The v1 term "studio" for the learner frontend is retired (ADR 0013).
- **One person, many apps.** A person sees an app launcher listing only the apps their role assignments open. A university lecturer can be a learner in the Learner App and an instructor in the Instructor App with one sign-in.
- **No app holds business rules.** Every permission is enforced by the API. An app's route guard only decides what to render.
- **App audience.** Each app is its own Clerk authorised party (`azp`). Some endpoints accept tokens only from specific apps (for example `platform.*` endpoints require the Admin App audience and MFA). See [Permissions and attributes](#permissions-and-attributes).
- **Shared design system.** All five apps use the stack in ADR 0012 and the shared packages in ADR 0014. Each app has its own navigation and density, not its own component library.
- **Future clients.** Native mobile apps (Learner first, then Instructor) and partner integrations are clients of the same API (ADR 0027).

## Tenancy model

A **tenant** is an **organisation**. "Institution" is the user-facing word for an education or workforce organisation; the data model says `organisation`.

```text
Platform
└── Organisation (tenant)            kind: consumer | university | college | school | enterprise | bootcamp | government | publisher
    ├── Campus (optional)
    │   └── Department (optional; may nest one level: faculty → department)
    │       └── Cohort
    └── Department (allowed directly under the organisation)
        └── Cohort
```

| Term | Definition |
| --- | --- |
| Organisation kind | `school` means an upper-secondary or further-education provider whose learners are 16 or older. The 16+ age rule applies to every kind; under-16 learners need a separate safeguarding model (open question, see [02-prd.md](02-prd.md)) |
| Organisation | The tenant. Owns licences, branding, SSO configuration, policies, cohorts, academic records, and optional private content. Table `tenancy.organisations`. Column `tenant_id` everywhere else |
| Consumer organisation | The built-in organisation (`kind = consumer`, slug `ai-mentor-public`) that every self-registered learner belongs to. B2C is a tenant like any other, so the code has no "no tenant" branch |
| Publisher organisation | The second built-in organisation (`kind = publisher`, slug `ai-mentor-content`). It owns the `master` workspace, so every authored row has a non-null `tenant_id`. Platform content roles are assigned in it |
| Campus | A physical or administrative site of an organisation. Optional |
| Department | An academic or business unit (faculty, school, department, team). Optional. At most two levels |
| Cohort | A group of learners taught together on a schedule by one or more instructors. Synonyms in UX: class, section, intake, group. Table `classroom.cohorts` |
| Org unit | Generic term for organisation, campus, department, or cohort when a rule applies to all of them. Org units form a tree stored as `ltree` |
| Membership | A person's link to an organisation, with status (`invited`, `active`, `suspended`, `left`). One person may have many memberships |
| Licence | A commercial grant from the platform to an organisation: plan, seat count, term, and entitlements. Seats are assigned to memberships |
| Workspace | A content ownership boundary in Content Studio. `master` is the platform-owned repository. An organisation may have an `org` workspace (licence feature) for its private content |

Tenancy rules:

1. Every tenant-scoped row carries `tenant_id`. PostgreSQL row-level security filters on it (`app.tenant_id`), in addition to the per-user policies in ADR 0011.
2. A request runs in exactly one **active tenant context**, chosen by the app (organisation switcher) and validated by the API against the person's memberships.
3. Platform staff act in the `platform` context, not inside a tenant. Reading tenant data from the platform context requires a recorded reason and is audited.
4. Organisation data never crosses tenants except through explicit, audited platform features (marketplace listings, de-identified benchmarks).

## Accounts and learner records

| Account type | Created by | Home tenant | Who controls the data (GDPR) | Can join other organisations |
| --- | --- | --- | --- | --- |
| `personal` | Self sign-up | Consumer organisation | AI Mentor (controller) | Yes, by invite or enrolment code; the learner consents to what each organisation may see |
| `managed` | Organisation provisioning (SSO JIT, SCIM, CSV import, instructor creation) | The provisioning organisation | The organisation (controller); AI Mentor is processor | No. Managed accounts live in one organisation |

Learner record rules (ADR 0021):

- **Learning record** (mastery, XP, streaks, badges, practice history, tutor conversations) belongs to the account. For a personal account it follows the learner across organisations. For a managed account it belongs to the organisation.
- **Academic record** (enrolments, cohort plans, assignments, submissions, grades, attendance, instructor notes) belongs to the organisation that issued the work, and is stored with that `tenant_id`.
- An organisation sees a personal-account member's learning record only for concepts in curricula it assigned, only while the membership is active, and only within the consent the learner gave at join time.
- A managed account can export its learning record as a portable **learning passport** (Open Badges 3.0 and a JSON transcript) if the organisation's policy allows it.

## Roles and scopes

A **role** is a named bundle of permissions. A **role assignment** is (person, role, scope). A person may hold many assignments. Roles are stored in PostgreSQL (`authz.role_assignments`); token claims never grant a role (carries forward SEC-02).

**Scope types**, outermost first: `platform` → `organisation` → `campus` → `department` → `cohort`. An assignment at a scope applies to that org unit and every unit below it. `workspace` is a separate scope type for Content Studio.

| Role ID | Scope types | App(s) | Summary |
| --- | --- | --- | --- |
| `learner` | organisation | Learner | Learns. Every member of an organisation who studies holds this role in that organisation. Cohort membership is a `classroom.cohort_members` row (a relationship attribute), not a cohort-scoped role assignment |
| `teaching_assistant` | cohort | Instructor | Marks submissions, views progress, messages learners in assigned cohorts. Cannot change plans. May be delegated grade release and grade overrides by a cohort instructor; a delegated override needs an instructor's approval before release |
| `instructor` | cohort, department | Instructor | Manages learners and plans in their cohorts, creates assessments, marks, releases grades, overrides AI grades |
| `lead_instructor` | cohort, department, campus | Instructor | Instructor powers plus creating cohorts, adding instructors and TAs to them, and approving grade overrides when policy requires |
| `department_admin` | department | Institution | Manages instructors, cohorts, and reporting for a department |
| `campus_admin` | campus | Institution | Same as department admin for a whole campus |
| `org_admin` | organisation | Institution | Manages the organisation: structure, members, instructors, cohorts, SSO, branding, policies, reporting |
| `org_owner` | organisation | Institution | `org_admin` plus contract, licences, deleting the organisation, and assigning `org_owner` and `org_admin`. At least one per organisation |
| `org_billing_manager` | organisation | Institution | Licences, seats, invoices, payment methods |
| `org_report_viewer` | organisation, campus, department | Institution | Read-only reporting and analytics |
| `org_compliance_officer` | organisation | Institution | Data requests, retention policy, consent records, compliance reports, audit log for the organisation |
| `content_author` | workspace | Content Studio | Creates and edits drafts: assets, lessons, modules, courses, paths, assessments, AI-generated drafts |
| `content_reviewer` | workspace | Content Studio | Reviews and approves others' content. Cannot approve own work |
| `content_publisher` | workspace | Content Studio | Publishes approved releases, schedules, archives, restores versions |
| `knowledge_steward` | workspace | Content Studio | Owns taxonomy, concept graph, metadata schema, and controlled vocabularies |
| `localisation_editor` | workspace | Content Studio | Translates and reviews localised content for assigned locales |
| `support_agent` | platform | Admin | Reads limited account, membership, and subscription data with a ticket reference |
| `finance_admin` | platform | Admin | Subscriptions, plans, licences, invoices, refunds |
| `ai_admin` | platform | Admin | Model registry, provider routing, prompt and policy releases, evaluation gates |
| `platform_operator` | platform | Admin | Feature flags, platform settings, jobs, incident tooling |
| `security_auditor` | platform | Admin | Read-only audit logs and security monitoring |
| `platform_admin` | platform | Admin, Content Studio (read, plus emergency take-down) | Everything in the Admin App, including role assignment at platform scope. In Content Studio: read everything, and take down published content in an emergency (`content.item:take_down`); no other content writes. Every action audited, MFA step-up for sensitive actions |
| `system` | platform | none | Non-human service principals (workers, webhooks, schedulers), each scoped to one function |

Mapping from v1 roles, used by the migration:

| v1 `users.role` | v2 assignments |
| --- | --- |
| `student` | `learner` in the consumer organisation |
| `instructor` | `content_author` in the `master` workspace (v1 instructors authored content), plus `learner` in the consumer organisation. They lose v1 platform analytics and see content analytics for their own items in Content Studio |
| `admin` | `platform_admin`, plus `content_reviewer`, `content_publisher`, and `knowledge_steward` in `master`, plus `learner` in the consumer organisation |
| v1 proposed `content_reviewer` | `content_reviewer` in `master` |
| v1 proposed `support` | `support_agent` |
| v1 proposed `content_manager` (`UseCases.md`) | `content_reviewer`, `content_publisher`, and `knowledge_steward` in `master` |

Guests (no account) can see the marketing site, the public catalogue, and the pseudonymous public leaderboard top 10.

## Permissions and attributes

**Permission format:** `<context>.<resource>:<action>`, lower snake case. Examples:

| Permission | Meaning |
| --- | --- |
| `learning.enrolment:create` | Enrol a learner |
| `classroom.cohort:create` | Create a cohort |
| `classroom.cohort_member:import` | Bulk import learners into a cohort |
| `classroom.cohort_plan:schedule` | Schedule a learning journey for a cohort |
| `assessment.submission:mark` | Mark a submission |
| `assessment.grade:override` | Override a grade, including an AI-proposed grade |
| `assessment.grade:release` | Release grades to learners |
| `content.course:publish` | Publish a course release |
| `knowledge.concept_relation:edit` | Edit the knowledge graph |
| `tenancy.sso_connection:configure` | Configure SSO for an organisation |
| `platform.feature_flag:edit` | Change a feature flag |
| `ai.model_route:edit` | Change model routing |
| `audit.log:read` | Read audit logs at the scope held |

**Decision rule** (ADR 0016): a request is allowed when the person holds a role assignment whose permissions include the action **and** whose scope contains the target resource **and** every applicable attribute condition passes. Deny by default. Explicit deny policies (for example a frozen assessment) win over allows.

**Attributes** the policy engine evaluates:

| Attribute | Examples |
| --- | --- |
| Subject | Account type, active tenant, role assignments, MFA freshness (`fva`), app audience (`azp`), licence seat, subscription tier, locale |
| Resource | `tenant_id`, org-unit path, owner, workspace, content state, data classification, assessment window, visibility |
| Relationship | Owner, cohort instructor of, TA of, member of, author of (for the two-person rule) |
| Context | Time, assessment integrity mode, IP allowlist for the organisation, consent granted, organisation policy flags |

## Content model

Knowledge hierarchy (from the smallest unit up):

```text
Knowledge Asset → Lesson → Module → Course → Learning Path
                     ▲
                 Concept (knowledge graph node). Lessons teach concepts; assessment items measure concepts.
```

| Term | Definition |
| --- | --- |
| Knowledge asset | A governed source: PDF, book, paper, lecture notes, slides, video, dataset, repository, external link, image, audio, assessment, lesson content. Versioned. Ingested into RAG when published |
| Lesson | The smallest unit a learner completes. Has a primary concept, objectives, a body per locale and teaching style, and linked assets and checks |
| Module | An ordered group of lessons and checks |
| Course | An ordered group of modules with outcomes, prerequisites, and assessments. The unit institutions assign and the unit that is released |
| Learning path | An ordered sequence of courses (and optionally standalone modules or projects) toward a goal or role, for example "Reinforcement Learning Engineer" |
| Concept | A node in the knowledge graph (for example `bellman-equation`). Mastery is measured per concept |
| Concept relation | A typed, weighted edge: `prerequisite_of`, `builds_on`, `related_to`, `part_of`, `applies_to`, `contrasts_with`. Prerequisite edges are acyclic |
| Content release | An immutable, published version of a course or learning path, with semantic version `MAJOR.MINOR.PATCH`. Cohorts pin to a release |
| Overlay | An instructor's or organisation's non-destructive customisation of a release for a cohort: reorder, hide, add supplementary items, set dates, add instructions. Overlays never change the master |
| Derived course | A copy of a master release in an organisation workspace, edited there, and tracking its upstream release so updates can be reviewed and merged |
| Workflow states | `draft → in_review → approved → published → archived`, with `changes_requested` back to `draft`. Same states for every content type (extends v1 `draft, review, approved, published, archived`; `review` is renamed `in_review`) |

**Ownership:** the master repository belongs to the platform content organisation (platform admins, SMEs, curriculum designers, content teams). Instructors consume and customise through overlays. Organisations with an `org` workspace own their private content and derived courses.

## Teaching and assessment vocabulary

| Term | Definition |
| --- | --- |
| Enrolment | A learner's registration in a course or path, in a tenant context, optionally through a cohort |
| Cohort plan | A scheduled learning journey for a cohort: a pinned course or path release, an overlay, and dated plan items (release date, due date, close date) |
| Plan item | One scheduled entry in a cohort plan (lesson, module, assignment, live session) |
| Practice | Ungraded or self-directed activity: quizzes, flashcards, daily challenges, coding lab. Feeds mastery and XP. Lives in `learning` |
| Assessment | Formal, graded work in an organisation: quiz, exam, assignment, project, coding assessment, written response. Lives in `assessment` |
| Assignment | An assessment issued to a cohort or learner with dates, attempts, and grading settings |
| Submission | A learner's response to an assignment |
| Rubric | Criteria and performance levels used to mark a submission, manually or with AI assistance |
| Proposed grade | An AI-generated mark with per-criterion rationale and evidence. Never visible to the learner until a human accepts or overrides it, unless the assignment is auto-graded (objective items) |
| Grade override | A human replacing an automatic or AI-proposed grade, with a reason. Audited |
| Gradebook | Per-cohort grades by learner and assignment |
| Risk signal | A computed indicator that a learner may fall behind: inactivity, missed due dates, falling mastery, low engagement. Shown to instructors with the evidence |
| Attendance | Presence at a scheduled live session or required activity window, recorded manually, by check-in, or from activity |
| Assessment integrity mode | A policy state during a graded assessment that restricts the AI mentor (no solution disclosure, no exam coach), and optionally other features |

## Shared platform services

The backend stays a **modular monolith with one worker** (ADR 0002, amended by ADR 0017). Each shared service below is a bounded-context module with its own package, schema, public interface, and events. Modules talk through in-process interfaces and domain events, never through each other's tables. Any module can be extracted later along these seams.

| Service | Module | Owns | Main consumers |
| --- | --- | --- | --- |
| Authentication | `identity` | Accounts, profiles, Clerk sync, sign-in flows including SSO and JIT provisioning. SSO connection configuration is stored by `tenancy` (`tenancy.sso_connections`); SCIM clients by `integration` | All apps |
| Authorization | `authz` | Roles, permissions, role assignments, policies, decision log | All modules |
| Tenancy | `tenancy` | Organisations, org units, memberships, branding, organisation policies | All apps |
| AI Tutor Engine | `tutor` | Mentor modes, personas, Socratic policy, conversations, agent orchestration | Learner, Instructor |
| Knowledge Engine | `knowledge` | Knowledge assets, taxonomy, knowledge graph, metadata | Content Studio, RAG, Personalisation |
| Content Platform | `content` | Lessons, modules, courses, paths, releases, overlays, workflow, localisation jobs | Content Studio, Learner, Instructor |
| RAG Platform | `retrieval` | Ingestion pipeline, chunks, embeddings lineage, retrieval, citations | Tutor, Search, Content Studio |
| Assessment Platform | `assessment` | Item bank usage, assignments, submissions, rubrics, marking, grades, gradebook | Instructor, Learner, Reporting |
| Learning Delivery | `learning` | Enrolments, cohort plan delivery, progress, mastery, practice, flashcards | Learner, Instructor |
| Classroom | `classroom` | Cohorts, cohort membership, schedules, attendance, risk signals | Instructor, Institution |
| Personalisation Engine | `personalisation` | Learner model, preferences, adaptive sequencing, recommendations | Tutor, Learner, Content |
| Gamification Platform | `gamification` | XP ledger, levels, streaks, points, badges, titles, challenges, competitions, leaderboards | Learner, Instructor, Institution |
| Analytics Platform | `analytics` | Event ingestion, metrics, learner and cohort analytics, warehouse feed | All apps |
| Reporting Platform | `reporting` | Report definitions, scheduled and on-demand reports, exports, localised rendering | Institution, Instructor, Admin, Learner |
| Notification Platform | `notification` | Channels (in-app, email, push, SMS later), templates per locale, preferences, digests | All modules |
| Communication Hub | `messaging` | Announcements, instructor–learner messages, cohort discussions | Instructor, Learner |
| Search Platform | `search` | Unified search index across catalogue, knowledge, people (scoped), help | All apps |
| Localisation | `i18n` | Locales, message catalogues, translation memory, locale fallback | All modules |
| Commerce | `commerce` | Consumer subscriptions, organisation licences, seats, invoices (Stripe) | Learner, Institution, Admin |
| Integration | `integration` | LTI 1.3, OneRoster, SCIM 2.0, xAPI/cmi5 export, outbound webhooks | Institution, external LMS |
| AI Gateway | `ai_gateway` | Model registry, provider routing, guardrails, prompt releases, cost metering, evaluation | Tutor, RAG, Assessment, Content |
| Audit and Compliance | `audit` | Audit trail, data access log, data subject requests, retention | Admin, Institution |
| Configuration | `config` | Feature flags, platform settings, organisation settings, rollout rules | All modules |

## Domain events

- Envelope: CloudEvents 1.0, JSON. Required extensions: `tenantid`, `actorid`, `correlationid`. Type format: `com.aimentor.<context>.<entity>.<verb_past>.v<n>`.
- Short name used in docs: `<context>.<entity>.<verb_past>`, for example `learning.lesson.completed`.
- Publication: transactional outbox table `events.outbox` in the same transaction as the change, relayed to the Azure Service Bus topic `domain-events` (ADR 0018). Delivery is at least once; consumers are idempotent on event `id`.
- Events carry ids and the minimum attributes consumers need, never free-text personal data.

Canonical events referenced across documents (not exhaustive):

| Event | Producer | Typical consumers |
| --- | --- | --- |
| `identity.account.created`, `identity.account.erased` | identity | tenancy, analytics, audit, retrieval (erasure) |
| `tenancy.membership.activated`, `tenancy.membership.ended` | tenancy | authz, commerce (seats), classroom |
| `classroom.cohort_member.added`, `classroom.cohort_plan.scheduled` | classroom | learning, notification |
| `learning.enrolment.created`, `learning.lesson.completed`, `learning.mastery.changed` | learning | gamification, analytics, personalisation, classroom (risk) |
| `assessment.assignment.published`, `assessment.submission.submitted`, `assessment.submission.ai_marked`, `assessment.grade.released`, `assessment.grade.overridden` | assessment | notification, gamification, analytics, reporting |
| `gamification.xp.awarded`, `gamification.badge.earned`, `gamification.level.reached` | gamification | notification, analytics |
| `content.release.published`, `content.release.archived`, `content.item.state_changed` | content | retrieval, search, learning, notification |
| `knowledge.asset_version.published`, `knowledge.concept_relation.changed` | knowledge | retrieval, personalisation, search |
| `tutor.message.flagged` | tutor | audit, Admin moderation queue |
| `authz.role_assignment.granted`, `authz.role_assignment.revoked` | authz | audit, notification, search (people index) |
| `commerce.licence.changed`, `commerce.subscription.changed` | commerce | authz (entitlements), tenancy |

## Personalisation, mentor, and language vocabulary

**Learner profile inputs:** persona, experience, education, goals, learning style, technical depth, pace, mathematical preference, language, career objectives.

**Five adjustable dimensions** (each stored as an ordinal; the UI shows a slider):

| Dimension | Scale (low → high) | v1 field it replaces |
| --- | --- | --- |
| `depth` | Beginner → Intermediate → Advanced → Expert → Researcher | technical depth |
| `pace` | Slow → Moderate → Fast → Intensive | learning speed |
| `approach` | Storytelling → Visual → Balanced → Formal → Mathematical | teaching style and mathematical depth |
| `register` | Professional → Balanced → Academic | industry vs research mode |
| `breadth` | Broad survey → Balanced → Deep specialist | breadth vs depth |

An instructor or organisation policy may **lock** or **bound** a dimension for a cohort (for example `register ≥ Academic` in a university course).

**Mentor modes** (the job the AI is doing): `tutor`, `mentor`, `research_supervisor`, `coding_coach`, `career_coach`, `exam_coach`. Each mode is an agent plus a policy profile (ADR 0022). v1 `socratic` and `direct` become a teaching technique setting inside `tutor`.

**Mentor persona** (how the AI presents): personality, teaching style, voice style, age appearance, gender presentation, accent preference, coaching style. Personas never change correctness, grounding, or safety rules.

**Locales:** `en` (default and fallback), `fr`, `es`. Five localisation surfaces: UI, learning content, AI responses, assessments, reports. A graded assessment item is used in a locale only after its translation is reviewed (`translation_status = approved`).

## Releases

All documents use these release labels and dates.

| Release | Window | Theme | v1 label it absorbs |
| --- | --- | --- | --- |
| **R1** Foundation and Learner MVP | Q4 2026 (weeks 1–12) | Learner App closed beta on the current scope, plus the foundations that are expensive to retrofit: `tenant_id` everywhere, scoped roles, monorepo, outbox, Content Studio split from the admin portal | v1 MVP |
| **R2** Public launch and Content Studio | Q1 2027 | Public B2C launch. Content Studio v1 (builders, releases, workflow, localisation). Admin App v1 | v1 R2 |
| **R3** Classrooms | Q2–Q3 2027 | Instructor App v1 and Institution App v1 with pilot institutions: cohorts, plans, assessments, rubrics, AI-assisted marking, licences, SSO, reporting | v1 R3 (partly) |
| **R4** Enterprise | Q4 2027 – Q1 2028 | SCIM, LTI 1.3 and OneRoster, data residency, advanced analytics and workforce reporting, white-label domains, Learner mobile apps | v1 R3 |
| **R5** Ecosystem | 2028 | Content marketplace, AI agent orchestration, Instructor mobile app, partner API | new |

## Identifier conventions

| Item | Convention | Example |
| --- | --- | --- |
| v2 requirement IDs | New prefixes below; existing v1 prefixes continue with numbers from 100 (`GAM-101`, `I18N-101`, `TUT-101`) | `TEN-004` |
| New requirement prefixes | `PLT` platform, `TEN` tenancy, `IAM` identity and SSO, `AUTHZ` authorisation, `LRN` Learner App, `INS` Instructor App, `ORG` Institution App, `ADM` Admin App, `CST` Content Studio, `KM` knowledge management, `KG` knowledge graph, `ASM` assessment, `PER` personalisation, `TUT` mentor (from 101), `NTF` notification, `MSG` communication, `SRCH` search, `ANL` analytics, `RPT` reporting (from 101), `LIC` licensing and commerce, `INT` integration, `EVT` events, `NFR` non-functional (from 101) | `INS-012` |
| Use case IDs | `UC-<app>-NN` with app letter `L` Learner, `I` Instructor, `O` Institution, `A` Admin, `C` Content Studio, `P` platform or system | `UC-I-04` |
| User story IDs | `US-<app>-NNN`; epics `EP-<app>NN` | `US-C-021`, `EP-I03` |
| ADRs | Four digits, continuing from 0012 | `ADR 0016` |
| Tables | `<schema>.<plural_snake>` | `classroom.cohorts` |
| API paths | `/api/v1/...`, kebab-case plural nouns, tenant-scoped resources under `/orgs/{org_id}` | `/api/v1/orgs/{org_id}/cohorts` |
| Events | See [Domain events](#domain-events) | `assessment.grade.released` |
| Feature flags | `<app_or_context>.<feature>` | `instructor.ai_marking` |
| PRD feature IDs | `<app>-FNN` with `L`, `I`, `O`, `A`, `C`, or `P` (platform capability). v1 `F1`–`F27` stay valid | `I-F06` |
| Risks and open questions | `RK-NN` and `OQ-NN` (v1 risk IDs `R1`–`R16` clash with release labels) | `RK-04` |

### Organisation policy keys

Organisation policies live in `tenancy.org_policies` as namespaced keys. Use these names.

| Key | Values (default first) | Meaning |
| --- | --- | --- |
| `leaderboards.public_participation` | `false`, `true` | Managed learners appear on `global` and `country` boards |
| `mentor.allowed_modes` | all released modes, or a subset | Mentor modes available to members |
| `mentor.persona_attributes` | `all`, `limited` | Whether age appearance, gender presentation, and accent are selectable |
| `grades.override_approval` | `none`, `lead_instructor` | Whether a grade override needs a second approver |
| `grades.regrade_may_lower` | `false`, `true` | Whether a regrade can lower a grade |
| `records.passport_export` | `true`, `false` | Whether managed accounts may export a learning passport |
| `members.instructor_can_create` | `true`, `false` | Whether instructors may create and import learners |
| `members.allow_personal` | `true`, `false` | Whether personal accounts may join by invite or code |
| `members.managed_by_default` | `false`, `true` | Whether new members are provisioned as managed accounts |
| `locale.default` | `en`, `fr`, `es` | Organisation default locale |
| `security.mfa_teaching_roles` | `lead_instructor`, `all`, `none` | Which teaching roles must use MFA |
| `security.ip_allowlist` | empty, CIDR list | Restrict Instructor and Institution App access |
| `tutor.transcript_access` | `false`, `true` | Whether `org_compliance_officer` may read a managed learner's tutor transcripts with a recorded reason (learners must be told at onboarding). Never applies to personal accounts |
| `seats.reclaim_inactive_days` | `0` (off), `30`–`365` | Reclaim seats from inactive members |

### Shared defaults

Configurable defaults that more than one document quotes. Change them here first.

| Setting | Default | Bound |
| --- | --- | --- |
| Learners per cohort | 1,000 | Organisation policy may raise to 5,000 |
| CSV import | UTF-8 CSV only, 5,000 data rows and 10 MB per file, dry run required before commit, formula-injection cells neutralised | Larger rosters use SCIM or OneRoster. XLSX is not accepted |
| Regrade request window | 14 days after grade release | Per assignment |
| Minimum participants for a leaderboard scope to display | 5 | Fixed |
| Report cell suppression | Aggregates over fewer than 10 learners are suppressed | Fixed |
| Break-glass access to tenant data | 60 minutes, read-only, reason required, organisation notified within 24 hours | Fixed |
| Model or prompt change rollout | Evaluation gate, then 5% canary for 24 hours | Canary 1–20% |
| Invitation expiry | 14 days | 1–30 days |
| Risk signal triggers | 7 days inactive; 2 missed due dates in 14 days; mastery drop of 15 points on an assigned concept; engagement below 30% of the cohort median | Per cohort |
| AI-marking second-marker sample | 10% of AI-accepted marks per assignment, minimum 5 | 5–100% |
| AI-marking live pause | Proposals pause when AI–human agreement (accepted, or edited within one rubric level) falls below 70% over the last 30 reviewed proposals, per rubric and per locale | 60–90% |
| AI-marking low-confidence threshold | Proposals below 0.6 confidence are flagged and not pre-selected | 0.5–0.9 |
| MFA freshness for sensitive actions | 15 minutes | Fixed |
| Managed accounts on global and country leaderboards | Off (organisation policy `leaderboards.public_participation`) | Organisation may enable |
| Content release auto-advance | PATCH releases reach pinned cohorts automatically unless an assessment in the plan is open; MINOR and MAJOR need instructor adoption | Fixed |
| Minimum learner age | 16 for every account and organisation kind | Exception for managed accounts aged 13–15 only after a safeguarding ADR (SRS CMP-108A, R4 candidate) |
| Learners aged 16–17 on global and country leaderboards | Off | Organisation policy may show them in organisation and cohort scopes |
| Leaderboard percentile | Hidden when fewer than 20 learners are eligible in the scope | Fixed |
| XP for a graded assessment | 30 XP on submission, independent of the grade | Configurable per platform |
| Holders of `org_owner` per organisation, and of `platform_admin` | At least 1, at most 5 | Fixed |
| Consent scopes for a personal account joining an organisation | `profile_basic` and `assigned_progress` required; `mastery_detail`, `tutor_summaries`, `leaderboard_listing` optional | Fixed list |
| Licence plans (pricing hypotheses in [02-prd.md](02-prd.md)) | `classroom` (25–500 seats), `campus` (500–50,000), `enterprise` (250+). Instructor, TA, and admin seats are free | n/a |

## Canonical data and API names

The database keeps the 12 schemas of ADR 0011 and adds 14, for 26 in total. Other documents use these names; [07-database-design.md](07-database-design.md) defines columns.

| Schema | New or existing | Key tables |
| --- | --- | --- |
| `tenancy` | new | `organisations`, `org_units`, `memberships`, `invitations`, `enrolment_codes`, `sso_connections`, `domains`, `branding`, `org_policies` |
| `authz` | new | `roles`, `permissions`, `role_permissions`, `role_assignments`, `delegations`, `policies`, `decision_log` |
| `classroom` | new | `cohorts`, `cohort_members`, `cohort_staff`, `cohort_plans`, `plan_items`, `live_sessions`, `attendance_records`, `risk_signals`, `interventions` |
| `assessment` | new | `assessments`, `assessment_items`, `assignments`, `rubrics`, `rubric_criteria`, `rubric_levels`, `submissions`, `submission_responses`, `marks`, `ai_mark_proposals`, `grades`, `grade_overrides`, `accommodations` |
| `personalisation` | new | `learner_models`, `dimension_settings`, `dimension_locks`, `mentor_personas`, `adaptive_decisions` |
| `commerce` | new | `plans`, `subscriptions` (moved from `identity`), `licences`, `seat_assignments`, `invoices` |
| `messaging` | new | `announcements`, `threads`, `thread_participants`, `messages` |
| `notification` | new | `templates`, `preferences`, `deliveries`, `digests` |
| `integration` | new | `lti_platforms`, `lti_deployments`, `lti_line_items`, `scim_clients`, `oneroster_syncs`, `webhook_endpoints`, `webhook_deliveries`, `xapi_exports` |
| `platform` | new | `feature_flags`, `flag_rules`, `settings`, `model_registry`, `model_routes`, `prompt_releases` |
| `events` | new | `outbox`, `inbox` (consumer de-duplication) |
| `search` | new | `documents` (unified, tenant-filtered search rows with a `tsvector`; vectors in Qdrant collection `search_v1`) |
| `reporting` | new | `report_definitions`, `report_schedules`, `report_runs` (files in Blob storage) |
| `i18n` | new | `translation_memory` (UI message catalogues ship as files in `@aimentor/i18n`; glossaries are `knowledge.vocabularies`) |
| `identity` | existing, extended | `users` gains `account_type` and `home_tenant_id`; `users.role` is removed after migration |
| `curriculum` | existing, extended | Adds `workspaces`, `course_releases`, `path_releases`, `release_items`, `overlays`, `derived_course_links`; `workspace_id` on every authored row |
| `knowledge` | existing, extended | `assets` gain `workspace_id`, `rights`, `licence_terms`; `asset_kinds` widened to the 13 asset types |
| `learning`, `chat`, `game`, `activity`, `analytics`, `audit`, `vector`, `ref`, `util` | existing | Gain `tenant_id` where rows are tenant-scoped; `game` gains `competitions`, `seasons`, `leaderboard_scopes` |

API roots (one API, `/api/v1`, resource-oriented; [08-api-specification.md](08-api-specification.md) defines operations):

| Root | Scope | Main callers |
| --- | --- | --- |
| `/api/v1/me/...` | The signed-in person across tenants (profile, memberships, app launcher, preferences, learning record) | All apps |
| `/api/v1/learn/...` | Learner experience in the active tenant (catalogue, enrolments, tutor, practice, gamification) | Learner App |
| `/api/v1/orgs/{org_id}/...` | Tenant administration and classroom resources (org units, members, cohorts, plans, assignments, gradebook, reports, licences, SSO) | Instructor App, Institution App |
| `/api/v1/content/...` | Content Studio resources in a workspace (assets, lessons, courses, paths, releases, taxonomy, graph, workflow) | Content Studio |
| `/api/v1/platform/...` | Platform governance (users, organisations, flags, models, audit, subscriptions) | Admin App only |
| `/api/v1/integrations/...`, `/lti/...`, `/scim/v2/...`, `/webhooks/...` | Standards endpoints and inbound webhooks | External systems |

The active tenant is sent as the `X-Org-Id` header on `/learn` and `/me` calls and as the path parameter on `/orgs/{org_id}` calls. The API rejects a mismatch.

### Resolved naming decisions

These settle conflicts between this vocabulary, the v1 DDL in `backend/db/schema`, and the v1 SRS. Migrations implement them; documents use the v2 form.

| Topic | v1 form | v2 rule |
| --- | --- | --- |
| Backend code layout | Layers in `backend/app/{domain,services,repositories,api}` | One package per module: `backend/app/modules/<module>/` with `domain/`, `models.py`, `repositories/`, `services/`, `api/`, and a public `interface.py` (ADR 0017). Shared kernel in `backend/app/core`; policy engine in `backend/app/domain/authz` |
| Module to schema ownership | n/a | `content` owns `curriculum`; `tutor` owns `chat`; `retrieval` owns `vector`; `gamification` owns `game`; `analytics` owns `activity` and `analytics`; `ai_gateway` owns `platform.model_registry`, `platform.model_routes`, `platform.prompt_releases`; `config` owns `platform.feature_flags`, `platform.flag_rules`, `platform.settings`; the shared kernel `app.core.events` owns `events`. Other modules own the schema of the same name. One table-level exception: `knowledge.ingestion_jobs` and `knowledge.chunks` are written only by `retrieval` repositories and are allow-listed in the schema-access fitness test |
| App audiences | n/a | Setting `APP_AUDIENCES` maps each Clerk authorised party (`azp`) to an app code name; endpoints declare the audiences they accept (ADR 0013) |
| Hosting region | ADR 0006 originally said UK South | West Europe is the home region, North Europe the recovery region (SRS CON-002, ADR 0006 amendment, decided 2026-10-13). A US regional deployment (East US 2) is an R4 data-residency option |
| Processes | One API process, no queue | One image, two commands: `api` and `worker` (`python -m app.worker`). The worker is new in R1 |
| Prerequisite edge direction | DDL type `prerequisite` stored as *from requires to* (`q-learning → mdp`) | Type `prerequisite_of` stored as *from is prerequisite of to* (`bellman-equation → q-learning`). The migration swaps `from` and `to`. Other mappings: `related → related_to`, `extends → builds_on`, `part_of` and `applies_to` unchanged, `contrasts_with` is new |
| Slugs | DDL check `^[a-z0-9_]+$`; catalogue uses hyphens | Kebab case `^[a-z0-9]+(-[a-z0-9]+)*$` for concept, lesson, course, path, and organisation slugs. The DDL check changes; `ltree` labels replace `-` with `_` |
| Workflow states | `draft, review, approved, published, archived` | `draft, in_review, approved, published, archived`. `changes_requested` is a transition (`in_review → draft` with a required comment), not a stored state |
| Leaderboard scope types | `global, country, region` | `global, country, region, organisation, cohort, friends` |
| Leaderboard periods | includes `daily` | `weekly, monthly, season, all_time`. A season is a calendar quarter. `daily` is kept for daily-challenge boards only |
| Enrolment table | `learning.enrollments` | Table name kept to avoid a rename migration. Permissions and events use `enrolment` (`learning.enrolment:create`, `learning.enrolment.created`) |
| Role source of truth | SRS SEC-005; `Security-Compliance.md` finding SEC-02 | Same rule, carried forward: PostgreSQL role assignments only; token claims never grant a role |
| Authored vs issued assessments | `curriculum.assessments` (authored) | `curriculum.assessments` stays: an authored assessment template, part of a content release. `assessment.assessments` is a tenant-owned assessment an instructor issues, created from a template or from scratch, with `source_template_id` |
| Difficulty scale | Quiz levels end in `phd`; asset difficulty has six levels | One five-level scale for content, items, and the `depth` dimension: `beginner, intermediate, advanced, expert, researcher`. v1 `phd` maps to `researcher` |
| Translation status | n/a | `not_started, machine_draft, in_review, approved, stale`. A trigger sets `stale` when the source-locale content changes; a stale translation must be re-approved. Graded use requires `approved` |
| Assessment integrity mode | n/a | Levels `off, standard, strict` |
| Mentor modes by release | n/a | R1 `tutor`, `coding_coach`, `career_coach` (v1 agents exist); R2 `mentor`, `research_supervisor`; R3 `exam_coach` and integrity mode; R4 voice style and accent |
| Asset kinds vs file formats | v1 KR-002 lists 17 types, mixing kinds and formats | 13 asset kinds (Content model above); file formats are a separate attribute of an asset version |
| Permission contexts vs modules | n/a | The permission context is the module name, with two short aliases: `ai` for `ai_gateway`, and `platform` for platform-governance actions served by `config` and the Admin App. Content Studio authoring of items uses `content`; issuing and marking uses `assessment` |
| Item bank ownership | `curriculum` question bank | `content` owns authored items, item translations, and their workflow (in `curriculum`). `assessment.assessment_items` are immutable snapshots of items inside an issued assessment |
| SSO email matches a personal account | n/a | Never merged silently. If organisation policy `members.allow_personal` is on, the person may link the personal account as a member after the consent screen. Otherwise the person is told the email belongs to a personal account and must change that account's email before a managed account is created |
| Local ports | learner 3000, admin 3001 | learner 3000, admin 3001, instructor 3002, institution 3003, studio 3004 |
| Package names | n/a | `@aimentor/<name>` (for example `@aimentor/ui`) |

## Glossary

| Term | Meaning |
| --- | --- |
| ABAC | Attribute-based access control. Conditions on subject, resource, relationship, and context attributes |
| App launcher | The cross-app menu showing the apps a person can open |
| BFF | Backend for frontend. The thin server layer in each Next.js app (server components and route handlers) that aggregates API calls. It holds no business rules |
| Bounded context | A module with its own model, schema, interface, and events |
| Controller / processor | GDPR roles. Who decides why and how personal data is processed, and who processes it on their behalf |
| Learning passport | A portable export of a learner's verified achievements and mastery |
| LTI 1.3 | IMS Learning Tools Interoperability. Lets AI Mentor launch from Canvas, Moodle, Blackboard, and Brightspace and return grades |
| OneRoster | IMS standard for rostering data (organisations, classes, enrolments) |
| SCIM 2.0 | Standard API for provisioning accounts from an identity provider |
| xAPI / cmi5 | Standards for recording learning activity statements for external learning record stores |
| Org unit | Organisation, campus, department, or cohort |
| Overlay | Non-destructive cohort or organisation customisation of a content release |
| Release (content) | Immutable published version of a course or path |
| Release (product) | One of R1–R5 above |
| Tenant context | The single organisation a request acts within |
