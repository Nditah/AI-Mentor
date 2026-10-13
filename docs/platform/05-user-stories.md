# AI Mentor user stories (v2.0)

| Field | Value |
| --- | --- |
| Document | 05 User stories |
| Version | 2.0 |
| Date | 13 October 2026 |
| Status | Draft for review. Target scope; most stories are not built |
| Owner | Product (CPO), with Learning (CLO) for teaching and assessment stories |
| Related | [README.md](README.md) (canonical vocabulary), [02-prd.md](02-prd.md), [03-srs.md](03-srs.md), [04-use-cases.md](04-use-cases.md), [10-rbac-matrix.md](10-rbac-matrix.md), [15-roadmap.md](15-roadmap.md), [v1 UseCases.md](../UseCases.md), [ADR 0013 to 0027](../adr/README.md) |

## Change record

| Area | What changed | Why | Impacted systems | Implementation implications |
| --- | --- | --- | --- | --- |
| Scope | Adds 51 epics and 209 stories across the five applications and the shared platform | The product is now five applications on one platform serving many organisations (ADR 0013) | All five apps, all modules | Backlog is organised by app; each epic has an owning module |
| Identifiers | v2 stories use `US-<app>-NNN` and epics `EP-<app>NN`. v1 `US-001` to `US-143` keep their numbers | The README identifier conventions; v1 IDs are referenced by tests and the v1 traceability table | Backlog tooling, test names | Test names cite the story ID. No v1 ID is reused or renumbered |
| Actors | Stories name the v2 role IDs (`instructor`, `org_admin`, `content_reviewer`) instead of v1 Student, Instructor, Content Manager, Administrator | Roles are scoped assignments, not a linear rank (ADR 0016) | `authz`, every API route | Every story with a protected action names the permission it needs |
| Workflow states | v1 `Review` is `in_review`; `changes_requested` is added | Same five states for every content type (README content model, ADR 0019) | `content`, Content Studio | v1 stories US-121 to US-126 are read with the new state names |
| Story template | Adds Size, Release, and Trace to the v1 Priority, Dependencies, and Use case fields | Multi-release planning across five apps needs size and release on every story | Planning, roadmap | Stories without a release are not ready |
| Acceptance criteria | Tenant isolation and permission checks are written into the criteria of every tenant-scoped story | Cross-tenant leakage is the highest-impact defect class in a multi-tenant system (ADR 0015) | API, PostgreSQL row-level security, tests | Each such story needs at least one cross-tenant negative test |
| Definition of ready and done | Adds five multi-tenant checks (tenant isolation, permission declared, events documented, i18n keys, accessibility) | Shared platform work must be safe for every organisation from the first release | All teams | See [Definition of ready and done additions](#12-definition-of-ready-and-done-additions) |

## Relationship to v1 documents

| v1 document or section | Status under v2 | Notes |
| --- | --- | --- |
| `UseCases.md` sections 7 to 11 (story conventions, Epics 1 to 16, traceability, delivery order, open questions) | Retained | The 143 v1 stories remain valid. Amendments are listed in [v1 epics under v2](#2-v1-epics-under-v2). Acceptance criteria not amended stay normative |
| `UseCases.md` business rules BR-01 to BR-24 | Retained except BR-01 | BR-01 (linear role rank) is superseded by scoped roles (ADR 0016). Other rules, such as XP values (BR-02), the daily cap (BR-03), and Socratic stages (BR-09), apply unchanged and are cited here |
| `UseCases.md` sections 2 and 3 (actors, permissions by role) | Superseded | Replaced by the README roles table and [10-rbac-matrix.md](10-rbac-matrix.md) |
| v1 use cases UC-01 to UC-38 | Retained | v2 use cases are `UC-<app>-NN` in [04-use-cases.md](04-use-cases.md) |

## Contents

1. [Story conventions](#1-story-conventions)
2. [v1 epics under v2](#2-v1-epics-under-v2)
3. [Learner App](#3-learner-app)
4. [Instructor App](#4-instructor-app)
5. [Institution App](#5-institution-app)
6. [Admin App](#6-admin-app)
7. [Content Studio](#7-content-studio)
8. [Platform](#8-platform)
9. [Traceability](#9-traceability)
10. [Stories by actor](#10-stories-by-actor)
11. [Suggested delivery order](#11-suggested-delivery-order)
12. [Definition of ready and done additions](#12-definition-of-ready-and-done-additions)
13. [Open questions](#13-open-questions)

---

## 1. Story conventions

v2 stories follow the v1 template in [UseCases.md section 7](../UseCases.md#7-story-conventions): a role, a goal, and a benefit, then metadata, then acceptance criteria written as Given / When / Then so they can be turned into tests. To keep 209 stories readable, the role, goal, and benefit sit on one line and the criteria follow the metadata line directly.

| Field | Values | Meaning |
| --- | --- | --- |
| Priority | Must, Should, Could | MoSCoW against the release in the Release field. **Must:** the release cannot ship without it. **Should:** part of the release; it can slip one sprint without blocking it. **Could:** valuable stretch; cut first if the release is at risk |
| Size | S, M, L, XL | Relative effort for one cross-functional pair. S up to 3 days; M 4 to 8 days; L 9 to 15 days; XL more than 15 days. An XL story is split before it enters a sprint |
| Release | R1 to R5 | The product release in the README. A story is planned in one release only |
| Dependencies | Story IDs or None | Stories that must be done first. v1 IDs (`US-074`) and v2 IDs (`US-L-003`) may both appear |
| Use case | `UC-<app>-NN` or v1 `UC-NN` | The use case the story realises in [04-use-cases.md](04-use-cases.md) |
| Trace | Requirement prefix areas | The requirement areas in [02-prd.md](02-prd.md) and [03-srs.md](03-srs.md) that the story satisfies, using the README prefixes (`TEN`, `INS`, `ASM`) and v1 prefixes continued from 101 (`GAM`, `I18N`, `TUT`, `RPT`) |

Use case references point to [04-use-cases.md](04-use-cases.md). A story lists every use case its epic realises. `v1 UC-NN` refers to `UseCases.md`. "none" means the epic has no dedicated use case.

Shared wording in acceptance criteria:

- **Another organisation** means a user whose active tenant context is a different organisation. A request for a resource in another organisation returns 404, so the API never confirms that the resource exists.
- **Outside my scope** means a user in the same organisation without a role assignment whose scope contains the resource. The API returns 403 and writes an entry to `authz.decision_log`.
- **Audited** means an entry in the audit trail with actor, action, target, before, after, time, tenant, and, for platform staff, the recorded reason.
- Times are in the cohort's timezone for cohort dates and in the learner's timezone for personal dates. "Within 1 minute" is measured from the committing transaction.

---

## 2. v1 epics under v2

Epics 1 to 16 and stories US-001 to US-143 remain valid. They now belong to an application:

| v1 epic | Stories | v2 application | Owning module(s) |
| --- | --- | --- | --- |
| 1. Accounts and access | US-001 to US-009 | Learner App (sign-up and sign-in are shared by every app) | `identity`, `authz` |
| 2. Onboarding and personalisation | US-010 to US-019 | Learner App | `personalisation` |
| 3. AI Tutor | US-020 to US-038 | Learner App | `tutor`, `retrieval`, `ai_gateway` |
| 4. Learning paths, recommendations, and study plans | US-039 to US-048 | Learner App | `learning`, `personalisation` |
| 5. Quizzes | US-049 to US-056 | Learner App (practice) | `learning` |
| 6. Coding lab | US-057 to US-064 | Learner App (practice) | `learning` |
| 7. Flashcards | US-065 to US-069 | Learner App | `learning` |
| 8. Daily challenges | US-070 to US-073 | Learner App | `gamification` |
| 9. Gamification and progress | US-074 to US-083 | Learner App | `gamification`, `learning` |
| 10. Leaderboards | US-084 to US-087 | Learner App | `gamification` |
| 11. Multilingual learning | US-088 to US-092 | Learner App (US-092 moves to Content Studio) | `i18n`, `content` |
| 12. Research assistant | US-093 to US-098 | Learner App | `tutor`, `retrieval` |
| 13. Career guidance | US-099, US-100 | Learner App | `tutor`, `personalisation` |
| 14. Plans and billing | US-101 to US-105 | Learner App | `commerce` |
| 15. Knowledge portal and content workflow | US-106 to US-131 | Content Studio | `knowledge`, `content`, `retrieval` |
| 16. Administration and operations | US-132 to US-143 | Admin App: US-132 to US-135, US-137, US-138, US-140 to US-143. Content Studio: US-136 (concept difficulty and gaps feed content planning; Admin App keeps a read-only global view) and US-139 is shared (triggered by an embedding model change in the Admin App, progress shown in Content Studio) | `platform`, `ai_gateway`, `audit`, `analytics` |

Amended v1 stories. The amendment wins over the v1 criterion it names; the rest of the story stands.

| v1 story | Amendment | v2 story that carries it |
| --- | --- | --- |
| US-006 | The webhook creates an account with `account_type = personal`, an active membership in the consumer organisation, and a `learner` role assignment, not a `student` role | US-L-001, US-P-003 |
| US-007 | Role rank checks become permission checks with scope and attributes (ADR 0016). "Higher role allowed" (BR-01) no longer applies. The test rule (one allowed and one denied case per route) becomes one allowed, one denied, and one cross-tenant case | US-P-001, US-P-002 |
| US-014 to US-017 | Teaching style, pace, depth, mathematics, and breadth become the five dimensions `depth`, `pace`, `approach`, `register`, `breadth`. Tutor personality becomes the mentor persona | US-L-015, US-L-017 |
| US-021, US-022 | Socratic and direct are a teaching technique inside the `tutor` mode, not modes of their own | US-L-016 |
| US-047, US-048 | Self-made study plans stay. A cohort plan, when present, takes precedence for dated items | US-L-005 |
| US-072, US-073 | The v1 actor Content Manager becomes `platform_operator` (challenge schedules, in the Admin App) and `content_author` (challenge items, in Content Studio) | US-L-024 |
| US-084 to US-087 | Global and country boards stay. Institution, cohort, and friends scopes are added, with per-scope visibility | US-L-021, US-L-022 |
| US-092 | Linking translations moves to the Content Studio localisation workflow | US-C-042 |
| US-101 to US-105 | Subscriptions move from `identity` to `commerce` | US-A-021 |
| US-106 to US-131 | v1 actor Content Manager becomes `content_author`, `content_reviewer`, `content_publisher`, or `knowledge_steward` in a workspace. v1 Instructor as author becomes `content_author` in `master` | US-C-001 to US-C-049 |
| US-121 to US-126 | State `Review` is renamed `in_review`. "Request changes" sets `changes_requested`, which returns the item to `draft` | US-C-033 to US-C-037 |
| US-123 | Self-approval prevention becomes the two-person rule on the "author of" relationship. The emergency override is held by `platform_admin` only, with MFA step-up | US-C-035 |
| US-124 | "An Instructor cannot publish" becomes "only `content_publisher` in the workspace can publish" | US-C-036 |
| US-130 | Incorrect and unclear flags stay in Content Studio. Unsafe flags go to the Admin App moderation queue (`tutor.message.flagged`) | US-A-025 |
| US-132 to US-134 | User administration acts in the platform context. Role changes become role assignments with scope; tenant data needs a recorded reason | US-A-001 to US-A-003 |
| US-137 to US-139 | Provider settings become the model registry, model routes, and prompt releases, held by `ai_admin` | US-A-009 to US-A-011 |
| US-142 | The audit log is readable at the scope held (`audit.log:read`), so organisations see their own entries | US-O-032, US-A-017 |

---

## 3. Learner App

The Learner App keeps every v1 learner story. The epics below add organisation context, classroom work, grades, mentor modes, the five dimensions, scoped competition, search, career planning, analytics, and full localisation.

### EP-L01 Organisations and tenant context

#### US-L-001 Belong to the consumer organisation by default
As a **self-registered learner**, I want **my account to sit in the public consumer organisation**, so that **I can learn without joining an institution**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-006 · **Use case:** UC-L-01, UC-L-02 · **Trace:** TEN, IAM
- Given a new personal sign-up, when `identity.account.created` is processed, then within 60 seconds an `active` membership in `ai-mentor-public` and a `learner` role assignment at organisation scope exist.
- Given a `/api/v1/learn` request without an `X-Org-Id` header, when the API handles it, then it returns 400 and no data is read.
- Given an enrolment, XP entry, or conversation created in this context, when the row is inspected, then its `tenant_id` is the consumer organisation's ID.

#### US-L-002 Join an organisation with an invitation or enrolment code
As a **learner with a personal account**, I want **to join my university with an invitation link or an enrolment code**, so that **I can take its courses and keep my existing progress**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-L-001, US-I-003 · **Use case:** UC-L-01, UC-L-02 · **Trace:** TEN, LRN
- Given a valid enrolment code, when I enter it, then I see the organisation name, the cohort, and exactly which parts of my learning record the organisation will see, and nothing is joined until I consent.
- Given I consent, when I confirm, then my membership is `active`, I hold `learner` at the cohort's scope, the consent version and time are stored, and `tenancy.membership.activated` is emitted.
- Given a code that has expired or reached its use limit, when I enter it, then I am told why and no membership is created.
- Given a managed account, when it opens an invitation from another organisation, then joining is refused.

#### US-L-003 Switch my active organisation
As a **learner with two memberships**, I want **an organisation switcher**, so that **each organisation's courses, cohorts, and leaderboards stay separate**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-L-002 · **Use case:** UC-L-01, UC-L-02 · **Trace:** TEN, LRN
- Given active memberships in organisations A and B, when I choose B, then later `/learn` calls send B's `X-Org-Id` and the catalogue, enrolments, assignments, and institution leaderboard show only B's data.
- Given a request with the `X-Org-Id` of an organisation where I have no active membership, when the API handles it, then it returns 403 and the denial is logged.
- Given a personal account, when I switch, then my XP, level, streak, badges, and concept mastery are unchanged.
- Given I sign in again on the same device, when the app loads, then my last active organisation is selected.

#### US-L-004 Leave an organisation
As a **learner with a personal account**, I want **to leave an organisation**, so that **it stops seeing my learning record**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-L-002 · **Use case:** UC-L-01, UC-L-02 · **Trace:** TEN, LIC
- Given I confirm leaving, when it is processed, then my membership is `left`, `tenancy.membership.ended` is emitted, and my seat is released within 5 minutes.
- Given I have left, when the organisation runs a report, then it shows none of my learning record after the leaving date, and my academic record (submissions, grades, attendance) stays with the organisation (ADR 0021).
- Given the consumer organisation, when I try to leave it, then the option is not shown because it is my home tenant.
- Given a managed account, when I look for "Leave", then it is not shown and only an `org_admin` can end the membership.

### EP-L02 Cohort plans and assignments

#### US-L-005 See my cohort plan
As a **cohort learner**, I want **a dated plan of what to study**, so that **I know what is due and when**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-011 · **Use case:** UC-L-03, UC-L-04 · **Trace:** LRN, INS
- Given a scheduled cohort plan, when I open my cohort, then plan items list in date order with release, due, and close dates and a status of not released, open, due soon (under 48 hours), overdue, or closed.
- Given the overlay hides a lesson, when the plan renders, then the lesson is absent; given it adds a supplementary item, then that item is labelled "Added by your instructor".
- Given a plan item whose release date is in the future, when I request its content, then the API returns 403 with the release date.
- Given the ID of a plan in another cohort, when I request it, then the API returns 404.

#### US-L-006 Study the release my cohort is pinned to
As a **cohort learner**, I want **my course to stay on the release my cohort is pinned to**, so that **content does not change during the term**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-010, US-C-036 · **Use case:** UC-L-03, UC-L-04 · **Trace:** LRN, CST
- Given my cohort is pinned to course release 2.1.0 and 2.2.0 is published, when I open the course, then I see 2.1.0.
- Given my instructor moves the cohort to 2.2.0, when I next open it, then completions for unchanged lessons carry over and a summary lists what changed.
- Given I am also self-enrolled in the same course in the consumer organisation, when I view both, then they are separate enrolments and concept mastery is shared because it belongs to my learning record.

#### US-L-007 Open and submit an assignment
As a **cohort learner**, I want **to open an assignment, see its rules, and submit my work**, so that **it is marked on time**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-016 · **Use case:** UC-L-03, UC-L-04 · **Trace:** ASM, LRN
- Given an open assignment, when I open it, then I see instructions, attempts allowed, time limit, due and close dates, weighting, and whether AI-assisted marking is used.
- Given I submit before the due date, when it saves, then I get a receipt with a timestamp and `assessment.submission.submitted` is emitted.
- Given I submit after the due date and before the close date with late submission allowed, when it saves, then it is marked late; after the close date the submission is refused with 409.
- Given I have used 2 of 2 attempts, when I try a third, then it is refused.

#### US-L-008 Know what the mentor can do during a graded assessment
As a **learner sitting a graded assessment**, I want **the mentor's limits to be visible**, so that **I do not break the rules by accident**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-016, US-L-013 · **Use case:** UC-L-03, UC-L-04 · **Trace:** ASM, TUT
- Given assessment integrity mode is active for me, when I open the mentor, then a banner states the restriction and `exam_coach` is unavailable.
- Given I ask for the answer to an item in the assessment, when the mentor replies, then it refuses to disclose the solution and the refusal is logged with the assessment ID.
- Given the assessment window closes, when 1 minute passes, then the restrictions lift.

### EP-L03 Grades and feedback

#### US-L-009 See released grades and feedback
As a **cohort learner**, I want **to see my grade, rubric levels, and comments once they are released**, so that **I know how I did and how to improve**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-021 · **Use case:** UC-L-05 · **Trace:** ASM, LRN
- Given `assessment.grade.released` for my submission, when 1 minute passes, then I see the score, the level for each rubric criterion, and comments, and I am notified.
- Given an AI-proposed grade not yet accepted by a human, when I open the submission, then the API returns no grade and the status reads "Marking in progress".
- Given the ID of another learner's submission, when I request it, then the API returns 404.

#### US-L-010 Understand how my grade was produced
As a **cohort learner**, I want **to know whether my grade was automatic, human, or AI-assisted**, so that **I can trust it**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-L-009, US-I-023 · **Use case:** UC-L-05 · **Trace:** ASM
- Given an accepted AI proposal, when I view the grade, then it reads "Marked with AI assistance and reviewed by" followed by the marker's name.
- Given an override, when I view the grade, then I see the final grade and feedback, and the AI proposal and override reason are not returned by the API.
- Given objective items only, when I view the grade, then it reads "Marked automatically".

#### US-L-011 Request a regrade
As a **cohort learner**, I want **to ask for a regrade with a reason**, so that **mistakes can be corrected**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-L-009 · **Use case:** UC-L-05 · **Trace:** ASM, INS
- Given a released grade and the organisation's regrade window (default 14 days), when I submit a reason of 20 to 1000 characters, then the cohort instructors are notified.
- Given the window has passed, when I open the grade, then the option is hidden and the API returns 409.
- Given an open regrade request on the submission, when I try to raise another, then it is refused.

#### US-L-012 See my gradebook
As a **cohort learner**, I want **all my grades for a cohort in one place**, so that **I can track my standing**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-L-009 · **Use case:** UC-L-05 · **Trace:** ASM, RPT
- Given my cohort, when I open the gradebook, then each assignment shows status, grade, and weight, and a running total uses the organisation's grading scheme.
- Given I export, when the file is produced, then it is a PDF in my locale with the organisation's branding.
- Given I belong to cohorts in two organisations, when I open the gradebook, then only the active organisation's cohorts are listed.

### EP-L04 Mentor modes and persona

#### US-L-013 Choose a mentor mode
As a **learner**, I want **to choose what job the mentor is doing**, so that **I get the right kind of help**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-020 · **Use case:** UC-L-06 · **Trace:** TUT, PER
- Given the mode picker, when it opens, then it lists `tutor`, `mentor`, `research_supervisor`, `coding_coach`, `career_coach`, and `exam_coach` with a one-line description in my locale.
- Given I choose `coding_coach`, when I send a message, then the reply comes from the coding coach agent and its policy profile, and the mode is stored on the message.
- Given a mode disabled by my organisation's policy or not in my entitlements, when I pick it, then it is shown as unavailable with the reason and the API returns 403.

#### US-L-014 Be offered a better mode
As a **learner**, I want **the mentor to suggest a different mode when my question fits it better**, so that **I do not have to know the modes in advance**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-L-013 · **Use case:** UC-L-06 · **Trace:** TUT
- Given I am in `tutor` and ask how to prepare a CV for a machine learning role, when the reply renders, then it offers to switch to `career_coach` with one action.
- Given I decline, when I continue, then the mode does not change and the suggestion is not repeated in that conversation.
- Given any suggestion, when it is made, then the mode never changes without my action.

#### US-L-015 Configure my mentor persona
As a **learner**, I want **to set how the mentor presents itself**, so that **I am comfortable learning with it**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-L-013 · **Use case:** UC-L-06 · **Trace:** TUT, PER
- Given the persona settings, when they open, then I can set personality, teaching style, voice style, age appearance, gender presentation, accent preference, and coaching style, with a preview reply.
- Given I change the persona, when I ask a question I asked before, then citations, grounding, Socratic stages (BR-09), and safety refusals are unchanged and only tone and presentation differ.
- Given my cohort allows only certain persona presets, when I open the settings, then only those presets are offered.

#### US-L-016 Choose Socratic or direct teaching inside the tutor mode
As a **learner**, I want **to choose between guided questions and direct answers while in tutor mode**, so that **v1 Socratic and Direct behaviour continues**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-021, US-022, US-L-013 · **Use case:** UC-L-06 · **Trace:** TUT
- Given tutor mode, when I open its settings, then the teaching technique is `socratic` by default and can be changed to `direct`.
- Given `socratic`, when I start a new concept, then the stages in BR-09 apply.
- Given my instructor locked the technique to `socratic` for the cohort, when I try to change it in that tenant context, then the control is disabled and names the cohort.

### EP-L05 Personalisation dimensions

#### US-L-017 Set my five dimensions
As a **learner**, I want **sliders for depth, pace, approach, register, and breadth**, so that **lessons and the mentor fit me**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-016 · **Use case:** UC-L-07 · **Trace:** PER
- Given the preferences page, when it loads, then each dimension shows its README scale, for example `depth` from Beginner to Researcher.
- Given I move `approach` to Mathematical, when I send the next mentor message, then that reply uses the new value.
- Given v1 preferences, when the migration runs, then technical depth maps to `depth`, learning speed to `pace`, teaching style and mathematical depth to `approach`, industry or research mode to `register`, and breadth to `breadth`, and no learner loses a setting.

#### US-L-018 See locked or bounded dimensions
As a **cohort learner**, I want **to see which dimensions my course has fixed**, so that **I understand why a slider is limited**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-L-017, US-I-008 · **Use case:** UC-L-07 · **Trace:** PER, INS
- Given my cohort bounds `register` to Academic or higher, when I open the slider, then values below Academic are disabled and a note names the cohort.
- Given I send a value outside the bound to the API, when it is validated, then it returns 422 and the stored value is unchanged.
- Given I switch to the consumer organisation, when I open preferences, then the cohort bound does not apply.

#### US-L-019 Review and correct my learner profile
As a **learner**, I want **to see and edit what the platform believes about me**, so that **recommendations are based on accurate facts**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-010 · **Use case:** UC-L-07 · **Trace:** PER
- Given my profile, when I open it, then it lists persona, experience, education, goals, learning style, technical depth, pace, mathematical preference, language, and career objectives, each editable.
- Given a recommendation, when I select "Why this?", then I see the adaptive decision that produced it and the inputs it used.
- Given I edit my goals, when I save, then the next recommendation request reflects the change.

#### US-L-020 Get adaptive sequencing inside a path
As a **learner**, I want **the path to adapt to what I already know**, so that **I neither repeat material nor skip foundations**.\
**Priority:** Should · **Size:** L · **Release:** R2 · **Dependencies:** US-044, US-079 · **Use case:** UC-L-07 · **Trace:** PER, LRN
- Given a lesson whose prerequisite concept is in the gap band (BR-08), when it is next, then the prerequisite lesson is recommended first.
- Given mastery of 75 or more on a lesson's primary concept, when the lesson is next, then I am offered a check quiz that marks it complete if I score 80% or more.
- Given a cohort plan, when sequencing runs, then required plan items are never reordered or skipped and only supplementary items are suggested.

### EP-L06 Scoped leaderboards, competitions, and challenges

#### US-L-021 See leaderboards for each scope
As a **learner**, I want **global, country, institution, cohort, and friends leaderboards**, so that **I can compare myself with the people who matter to me**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-084, US-085 · **Use case:** UC-L-08, UC-P-03 · **Trace:** GAM
- Given the leaderboards page, when it loads, then global and country show the top 10, and every scope shows rank, percentile, XP, achievements, and streak, plus my own row if I am outside the top 10.
- Given the institution and cohort tabs, when I am in the consumer organisation, then they are not shown; in organisation B they show only B's members.
- Given the public global board, when a guest views it, then entries use pseudonymous display names.
- Given a period selector, when I choose this week, this month, this season, or all time, then the ranking recomputes for that period.

#### US-L-022 Control my visibility on each board
As a **learner**, I want **to choose which boards show me**, so that **I compete only where I want to**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-087, US-L-021 · **Use case:** UC-L-08, UC-P-03 · **Trace:** GAM, TEN
- Given visibility settings, when I hide myself from global and country, then I am absent from both within 5 minutes and still see my own rank privately.
- Given my organisation's policy disables the institution board, when I open leaderboards in that context, then the tab is absent and the API returns 403.
- Given a managed account, when the organisation's policy sets cohort visibility on, then the learner cannot opt into the global board unless the policy allows it.

#### US-L-023 Add friends for a friends board
As a **learner**, I want **to connect with friends**, so that **we can follow each other's progress**.\
**Priority:** Could · **Size:** M · **Release:** R2 · **Dependencies:** US-L-021 · **Use case:** UC-L-08, UC-P-03 · **Trace:** GAM
- Given I send a friend request by invite link, when the other learner accepts, then each appears on the other's friends board; unaccepted requests show nothing.
- Given I have 200 friends, when I send another request, then it is refused.
- Given a managed account whose organisation disallows friend connections, when it opens a friend link, then the request is refused.

#### US-L-024 Join weekly and seasonal challenges
As a **learner**, I want **weekly and seasonal challenges beyond the daily ones**, so that **I have longer goals to work toward**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-070, US-071 · **Use case:** UC-L-08, UC-P-03 · **Trace:** GAM
- Given a weekly challenge, when Monday 00:00 UTC arrives, then a new set starts and the previous set closes.
- Given a seasonal challenge that runs for the calendar quarter, when I open it, then I see my progress, the end date, and the reward.
- Given I complete a challenge, when the reward is applied, then the XP respects the daily cap (BR-03) and the badge is awarded once.

#### US-L-025 Enter a competition
As a **learner**, I want **to enter a time-boxed competition at platform, organisation, or cohort scope**, so that **I can test myself against others**.\
**Priority:** Could · **Size:** L · **Release:** R3 · **Dependencies:** US-L-021, US-I-008 · **Use case:** UC-L-08, UC-P-03 · **Trace:** GAM
- Given a competition open for entry, when I join before its start time, then I appear on its board; after the start time, late entry follows the competition's rule.
- Given a cohort competition, when a learner outside the cohort requests it, then the API returns 404.
- Given the competition ends, when 24 hours of review pass, then results become final and excluded entries (US-141) are listed only to staff.

### EP-L07 Knowledge search

#### US-L-026 Search the catalogue and the knowledge base
As a **learner**, I want **one search box for courses, paths, lessons, concepts, and resources**, so that **I find material quickly**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-P-014 · **Use case:** UC-L-09 · **Trace:** SRCH
- Given a query, when results return, then they are grouped by type and the 95th percentile response time is under 500 milliseconds.
- Given content not `published`, or not in my entitlements, when I search, then it is not returned.
- Given a concept result, when I open it, then I see my mastery band and the lessons that teach it.

#### US-L-027 Get a cited answer card
As a **learner**, I want **a short grounded answer at the top of search results**, so that **simple questions do not need a full conversation**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-L-026, US-024 · **Use case:** UC-L-09 · **Trace:** SRCH, TUT
- Given a question-shaped query, when retrieval finds sources, then the card cites at least one published source.
- Given no grounded source, when the card would render, then it says the answer is not from the library (US-025) or is not shown.
- Given the card, when I select "Ask the mentor", then a conversation opens with the query and sources attached.

#### US-L-028 Search only what my organisation can see
As an **organisation learner**, I want **search to include my organisation's private content and nobody else's**, so that **results are relevant and private content stays private**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-P-015, US-C-004 · **Use case:** UC-L-09 · **Trace:** SRCH, TEN
- Given organisation A's private lesson, when a member of A searches its title, then it is returned.
- Given a member of organisation B, when they search the same title, then it is not returned and the result count does not include it.
- Given an automated test seeding private content in two organisations, when it runs, then no query in one returns content from the other.

#### US-L-029 Search in my language
As a **French-speaking learner**, I want **results in French first**, so that **I read in my language when I can**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-L-026 · **Use case:** UC-L-09 · **Trace:** SRCH, I18N
- Given my locale is `fr`, when I search, then `fr` content ranks above its `en` equivalent.
- Given only `en` exists for a result, when it shows, then it is labelled "English".
- Given a query in Spanish, when I search with locale `en`, then Spanish content is still matched.

### EP-L08 Career planning and learning passport

#### US-L-030 See the gap to a target role
As a **learner**, I want **to choose a target role and see the concepts I still need**, so that **I know how far I am from it**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-099, US-079 · **Use case:** UC-L-10, UC-L-11 · **Trace:** LRN, PER
- Given a target role such as "Reinforcement Learning Engineer", when I select it, then its required concepts list with my mastery band for each.
- Given the gap list, when it renders, then concepts are ordered by prerequisite depth and suggested paths are shown.
- Given I change my career objective in my profile, when I open career planning, then the target role suggestion updates.

#### US-L-031 Turn the gap into a dated career plan
As a **learner**, I want **milestones with dates**, so that **I can reach the role in the time I have**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-L-030, US-019 · **Use case:** UC-L-10, UC-L-11 · **Trace:** LRN, TUT
- Given my available hours per week and `pace`, when I create a plan, then milestones are dated and the end date is shown.
- Given I fall more than 2 weeks behind, when the weekly check runs, then `career_coach` offers to reschedule.
- Given a plan, when I accept a reschedule, then later milestones move and earlier completions stay.

#### US-L-032 Export my learning passport
As a **learner**, I want **a portable record of my verified achievements**, so that **I can show employers and other institutions**.\
**Priority:** Should · **Size:** L · **Release:** R4 · **Dependencies:** US-077 · **Use case:** UC-L-10, UC-L-11 · **Trace:** LRN, INT
- Given a personal account, when I export, then I receive Open Badges 3.0 credentials for badges and completions and a signed JSON transcript of mastery.
- Given a managed account whose organisation's policy forbids export, when I look for export, then it is hidden and the API returns 403.
- Given an exported credential, when a verifier checks it, then the signature validates against the published key.

#### US-L-033 Share a verifiable achievement
As a **learner**, I want **a link that proves one achievement**, so that **I share only what I choose**.\
**Priority:** Could · **Size:** S · **Release:** R4 · **Dependencies:** US-L-032 · **Use case:** UC-L-10, UC-L-11 · **Trace:** LRN
- Given I share a badge, when someone opens the link, then they see the credential fields only and no other profile data.
- Given I revoke the link, when it is opened, then it returns 404 within 1 minute.
- Given an expired credential, when the link is opened, then it is shown as expired.

### EP-L09 Learner analytics

#### US-L-034 See my learning analytics
As a **learner**, I want **trends of my effort and mastery**, so that **I can see what is working**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-080 · **Use case:** v1 UC-20 · **Trace:** ANL, LRN
- Given my analytics page, when it loads, then it shows time on task per week, mastery trend per concept, an activity heatmap, and quiz accuracy by difficulty for the last 12 weeks.
- Given a personal account with two memberships, when I view analytics, then my learning record is combined and academic data (grades, attendance) appears only in the issuing organisation's context.
- Given no activity in a week, when the chart renders, then that week shows zero rather than being omitted.

#### US-L-035 Compare myself with my cohort anonymously
As a **cohort learner**, I want **to see where I stand in my cohort without seeing others' data**, so that **I can judge my pace**.\
**Priority:** Could · **Size:** S · **Release:** R3 · **Dependencies:** US-L-034 · **Use case:** v1 UC-20 · **Trace:** ANL
- Given my cohort, when I open the comparison, then I see the cohort median and my percentile for progress and mastery.
- Given a cohort with fewer than 10 learners, when the comparison would show, then it is hidden.
- Given the comparison, when the API returns it, then it contains no other learner's identifier.

#### US-L-036 Get a localised weekly insight
As a **learner**, I want **a weekly summary in my language**, so that **I keep momentum**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-082, US-P-010 · **Use case:** v1 UC-20 · **Trace:** ANL, NTF
- Given Monday 08:00 in my timezone, when the digest runs, then I receive XP gained, concepts improved, streak, and one suggested next step, in my locale.
- Given I turned off weekly insight, when the digest runs, then nothing is sent.
- Given a cohort learner, when the insight is built, then upcoming due dates for the next 7 days are included.

#### US-L-037 See what each organisation can see about me
As a **learner with a personal account**, I want **a transparency page per organisation**, so that **I know what I have shared**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-L-002 · **Use case:** v1 UC-20 · **Trace:** TEN, ANL
- Given my memberships, when I open privacy settings, then each organisation lists the consent I gave, the date, and the concepts in its assigned curricula.
- Given an organisation, when I select "What they see", then I see the same fields its reports show about me.
- Given I want to withdraw, when I select it, then I am taken to US-L-004 with the consequences stated.

### EP-L10 Localisation of all surfaces

#### US-L-038 Use the whole Learner App in French or Spanish
As a **learner**, I want **every screen in my language**, so that **nothing breaks my concentration**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-088 · **Use case:** v1 UC-22 · **Trace:** I18N
- Given locale `fr` or `es`, when any screen renders, then every string comes from the message catalogue and dates, numbers, and currency use that locale's format.
- Given a key missing in `es`, when it renders, then the `en` string is shown and the missing key is logged once per release.
- Given a release build, when the catalogue check runs, then it fails if any key exists in `en` but not in `fr` or `es`.

#### US-L-039 Take assessments in my language only when reviewed
As a **learner**, I want **graded questions in my language only when a human has reviewed the translation**, so that **I am not marked on a mistranslation**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-C-044 · **Use case:** v1 UC-22 · **Trace:** I18N, ASM
- Given an item with `fr` `translation_status = approved`, when I sit the assessment in `fr`, then it is shown in French.
- Given an item without an approved `fr` translation, when I sit the assessment, then it is shown in `en` with a notice.
- Given I start an attempt, when I change the interface locale mid-attempt, then item text stays in the locale the attempt started with.

#### US-L-040 Receive reports and messages in my language
As a **learner**, I want **emails, certificates, and reports in my language**, so that **I can use them**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-P-010 · **Use case:** v1 UC-22 · **Trace:** I18N, RPT, NTF
- Given locale `es`, when a notification email is sent, then the subject and body use the `es` template.
- Given a certificate, when it is generated, then names of courses use their `es` title if it exists and `en` otherwise.
- Given I change my locale, when the next weekly insight is sent, then it uses the new locale.

#### US-L-041 Start in my organisation's default language
As a **managed learner**, I want **the app to open in my organisation's language on first sign-in**, so that **I do not have to find the setting**.\
**Priority:** Could · **Size:** S · **Release:** R3 · **Dependencies:** US-O-001 · **Use case:** v1 UC-22 · **Trace:** I18N, TEN
- Given an organisation default locale `fr`, when a managed learner signs in for the first time, then the interface is in French.
- Given the learner changes to `en`, when they sign in again, then `en` is kept unless the organisation's policy locks the locale.
- Given a personal account joining that organisation, when it joins, then its own locale is not changed.

---

## 4. Instructor App

The Instructor App is new in R3. Its users hold `instructor`, `lead_instructor`, or `teaching_assistant` at cohort, department, or campus scope. Every story acts in one organisation, sent as the `{org_id}` path parameter.

### EP-I01 Learner management: create, bulk import, invite

#### US-I-001 Create a learner account
As an **instructor**, I want **to create a learner account and add it to my cohort**, so that **learners without an account can start on day one**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-006, US-P-001 · **Use case:** UC-I-01, UC-I-02 · **Trace:** INS, TEN, IAM
- Given a cohort I teach and the organisation policy allowing instructors to create accounts, when I enter name, email, and optional external ID, then a `managed` account, an active membership, and a `learner` assignment at cohort scope are created, and a welcome email is sent in the cohort locale.
- Given the email already belongs to a member of my organisation, when I submit, then that member is added to the cohort and no duplicate is created.
- Given the email belongs to a personal account, when I submit, then I am offered an invitation instead and am told nothing about the account's other memberships.
- Given the organisation has no free seats, when I submit, then the API returns 409 and names the `org_billing_manager` contact.
- Given a cohort I do not teach, when I call `POST /api/v1/orgs/{org_id}/cohorts/{cohort_id}/members`, then it returns 403.

#### US-I-002 Bulk import learners from a CSV file
As an **instructor**, I want **to import a class list**, so that **I do not create learners one by one**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-001 · **Use case:** UC-I-01, UC-I-02 · **Trace:** INS, TEN
- Given the template with `email`, `given_name`, `family_name`, `external_id`, `locale`, and `cohort_code`, when I upload up to 5,000 data rows (10 MB), then a preview shows rows to create, rows to add, and rows with errors, and nothing is written yet.
- Given I confirm, when the import job finishes, then I receive a result file with one outcome per row and `classroom.cohort_member.added` is emitted once per added learner.
- Given I upload the same file again, when it runs, then no duplicates are created, matching on email or `external_id`.
- Given a row whose `cohort_code` names a cohort outside my scope, when the preview runs, then that row is rejected and the others are unaffected.

#### US-I-003 Invite learners by email or enrolment code
As an **instructor**, I want **to invite learners by email or share an enrolment code**, so that **learners with existing accounts can join**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-006 · **Use case:** UC-I-01, UC-I-02 · **Trace:** INS, TEN, NTF
- Given I invite an email, when the invitation is sent, then it expires after 14 days and shows as `invited` until accepted.
- Given I create an enrolment code, when I set a use limit of 60 and an expiry date, then the code stops working at either limit.
- Given an outstanding invitation, when I revoke it, then its link returns an "invitation no longer valid" page.

#### US-I-004 Find and filter my learners
As an **instructor**, I want **one list of the learners I teach**, so that **I can act on the right people quickly**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-001 · **Use case:** UC-I-01, UC-I-02 · **Trace:** INS
- Given my cohorts, when I open learners, then I can search by name or email and filter by cohort, membership status, risk level, and last active date.
- Given a `teaching_assistant`, when they open the list, then they can view it and the edit actions are absent.
- Given a learner who is only in cohorts I do not teach, when I request their profile by ID, then the API returns 403.

#### US-I-005 Move or remove a learner
As an **instructor**, I want **to move a learner to another cohort or remove them from mine**, so that **class lists stay accurate**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-I-004 · **Use case:** UC-I-01, UC-I-02 · **Trace:** INS, ASM
- Given I move a learner to another cohort in my scope, when it saves, then submissions and grades stay attached to the original cohort's assignments and the move is audited.
- Given I remove a learner from my cohort, when it saves, then their cohort membership ends and their organisation membership is unchanged.
- Given a learner with submissions awaiting marking, when I remove them, then I am warned with the count before confirming.

### EP-I02 Cohort management

#### US-I-006 Create a cohort
As a **lead instructor**, I want **to create a cohort**, so that **I can teach a group on a schedule**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-002 · **Use case:** UC-I-03 · **Trace:** INS, TEN
- Given `classroom.cohort:create` at a department, when I enter name, code, start and end dates, timezone, locale, and capacity, then the cohort is created under that department and `classroom.cohort.created` is emitted.
- Given an `instructor` without `lead_instructor`, when they try to create a cohort, then the API returns 403.
- Given a cohort code already used in the organisation, when I save, then it is refused.

#### US-I-007 Add co-instructors and teaching assistants
As a **lead instructor**, I want **to add staff to a cohort**, so that **marking and support are shared**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-I-006 · **Use case:** UC-I-03 · **Trace:** INS, AUTHZ
- Given a member of my organisation, when I add them as `instructor` or `teaching_assistant`, then a role assignment at the cohort scope is created and they can open the cohort within 60 seconds.
- Given I delegate grade release to a teaching assistant, when they release grades, then it succeeds for this cohort only.
- Given a person who is not a member of the organisation, when I search for them, then they are not found.

#### US-I-008 Configure cohort settings within organisation policy
As a **lead instructor**, I want **to set cohort rules**, so that **the cohort fits my course**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-006, US-O-008 · **Use case:** UC-I-03 · **Trace:** INS, PER, GAM
- Given cohort settings, when I open them, then I can set leaderboard visibility, allowed mentor modes, dimension locks and bounds, AI-assisted marking, and the late policy.
- Given the organisation's policy disables AI-assisted marking, when I try to enable it, then the control is disabled and the API returns 403.
- Given I tighten a setting the organisation allows, when I save, then it applies to the cohort's learners on their next request.

#### US-I-009 Archive and clone a cohort
As a **lead instructor**, I want **to archive a finished cohort and clone its plan for the next intake**, so that **I reuse my work**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-011 · **Use case:** UC-I-03 · **Trace:** INS
- Given a cohort past its end date, when I archive it, then it becomes read-only and its gradebook stays readable.
- Given I clone it with a new start date, when the copy is created, then the release, overlay, and plan items are copied with every date shifted by the same offset, and no members are copied.
- Given an archived cohort, when anyone tries to submit to it, then the API returns 409.

### EP-I03 Curriculum assignment and scheduling with overlays

#### US-I-010 Assign a course or path release to a cohort
As an **instructor**, I want **to assign a published course or path to my cohort**, so that **my learners study the right material**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-C-036, US-I-006 · **Use case:** UC-I-04, UC-I-14 · **Trace:** INS, LRN, CST
- Given the catalogue, when I browse, then I see `master` releases in my organisation's licence and releases in my organisation's workspace only.
- Given I assign course release 2.1.0, when it saves, then the cohort is pinned to 2.1.0 and an enrolment is created for each member with `learning.enrolment.created`.
- Given a release from another organisation's workspace, when I request it by ID, then the API returns 404.

#### US-I-011 Schedule a learning journey
As an **instructor**, I want **to give plan items release, due, and close dates**, so that **the cohort works to a timetable**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-010 · **Use case:** UC-I-04, UC-I-14 · **Trace:** INS, LRN
- Given `classroom.cohort_plan:schedule`, when I set dates in a calendar view, then they are stored in the cohort timezone and `classroom.cohort_plan.scheduled` is emitted.
- Given I shift all dates after a chosen item by 7 days, when I confirm, then every later item moves and learners are notified once.
- Given a due date before its release date, when I save, then it is refused.
- Given a `teaching_assistant`, when they try to change dates, then the API returns 403.

#### US-I-012 Customise a release with an overlay
As an **instructor**, I want **to reorder, hide, and add material for my cohort**, so that **the course fits my learners without changing the master**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-010 · **Use case:** UC-I-04, UC-I-14 · **Trace:** INS, CST
- Given an overlay, when I reorder modules, hide a lesson, add a published library resource, and add instructions, then my cohort sees the result and the master release content checksum is unchanged.
- Given I hide a lesson that teaches a course outcome, when I save, then I am warned which outcome loses coverage.
- Given an overlay, when I save it, then a new overlay version is stored and the previous one can be restored.

#### US-I-013 Review and adopt a new release
As an **instructor**, I want **to be told when a newer release of my course exists and adopt it on my terms**, so that **corrections reach my cohort without disruption**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-012, US-C-031 · **Use case:** UC-I-04, UC-I-14 · **Trace:** INS, CST, NTF
- Given `content.release.published` for a course my cohort is pinned to, when it is processed, then I am notified with the release notes and version.
- Given I adopt it now or at a date, when the move happens, then my overlay is reapplied and items it referenced that no longer exist are listed as conflicts.
- Given a PATCH release, when the organisation's policy enables automatic adoption of patches, then the cohort moves without my action and I am notified.

### EP-I04 Assessment creation and quiz builder

#### US-I-014 Build a quiz from the item bank
As an **instructor**, I want **to build a quiz from approved items**, so that **I assess with reviewed questions**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-C-017 · **Use case:** UC-I-05 · **Trace:** ASM, INS
- Given the item bank, when I search, then I can filter by concept, difficulty, type, and locale, and only `published` items are returned.
- Given a draw rule of 10 items from a pool of 30, when each learner starts, then each receives 10 items drawn from that pool.
- Given an item frozen because it is in a live assessment elsewhere, when I add it, then it is added read-only.

#### US-I-015 Write my own items
As an **instructor**, I want **to write items for my cohort**, so that **I can assess local topics**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-014 · **Use case:** UC-I-05 · **Trace:** ASM
- Given the item editor, when I save an item, then it is stored with my organisation's `tenant_id`, linked to a concept, and is not added to `master`.
- Given my organisation has an `org` workspace, when I choose "Propose to workspace", then a `draft` copy is created there for review.
- Given another organisation, when it searches the item bank, then my item is never returned.

#### US-I-016 Create an assignment
As an **instructor**, I want **to issue an assessment with dates and grading settings**, so that **learners know the rules and marking is consistent**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-014, US-I-018 · **Use case:** UC-I-05 · **Trace:** ASM, INS
- Given an assessment, when I set attempts, time limit, release, due and close dates, weighting, marking mode (automatic, manual, or AI-assisted), and integrity mode, then they are validated and saved.
- Given I publish, when it commits, then `assessment.assignment.published` is emitted and learners are notified at the release date.
- Given a learner has submitted, when I try to change the rubric or the item list, then it is refused and I am offered a new version for learners who have not started.

#### US-I-017 Set accommodations for individual learners
As an **instructor**, I want **to give extra time or later dates to learners who need them**, so that **assessment is fair**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-I-016 · **Use case:** UC-I-05 · **Trace:** ASM
- Given a learner, when I grant 25% or 50% extra time or a later due date, then their attempt uses it automatically.
- Given an accommodation, when other learners view the assignment, then it is not visible to them.
- Given an accommodation, when it is changed, then the change is audited.

### EP-I05 Rubrics and manual marking

#### US-I-018 Create a rubric
As an **instructor**, I want **criteria and performance levels**, so that **marking is consistent and explainable**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** None · **Use case:** UC-I-06, UC-I-07 · **Trace:** ASM
- Given the rubric editor, when I add criteria with weights and levels with points and descriptors, then the weights must total 100%.
- Given a rubric in my organisation's rubric library, when I reuse it, then a copy is attached to my assessment.
- Given marking has started, when I edit the rubric, then a new version is created and existing marks keep the version they used.

#### US-I-019 Mark a submission with a rubric
As an **instructor or teaching assistant**, I want **a marking view with the rubric beside the work**, so that **I mark quickly and fairly**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-018, US-L-007 · **Use case:** UC-I-06, UC-I-07 · **Trace:** ASM, INS
- Given `assessment.submission:mark` on the cohort, when I pick a level per criterion and add comments, then the mark autosaves every 10 seconds.
- Given a queue, when I finish a submission, then the next unmarked one opens.
- Given a submission from a cohort I am not staff on, when I open it by ID, then the API returns 403.

#### US-I-020 Mark anonymously and moderate a sample
As a **lead instructor**, I want **anonymous marking and second marking of a sample**, so that **marking is free of bias and consistent across markers**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-019 · **Use case:** UC-I-06, UC-I-07 · **Trace:** ASM
- Given anonymous marking, when markers open submissions, then learner names are replaced by a candidate number until grades are released.
- Given a moderation sample of 10%, when first marking completes, then that share of submissions is assigned to a second marker who cannot see the first mark.
- Given a difference of more than 10 percentage points, when both marks exist, then the submission is flagged for agreement.

#### US-I-021 Release grades
As an **instructor**, I want **to release grades when I am ready**, so that **learners see them all at once**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-I-019 · **Use case:** UC-I-06, UC-I-07 · **Trace:** ASM, NTF
- Given `assessment.grade:release`, when I release an assignment, then all accepted grades become visible and one `assessment.grade.released` event per grade is emitted.
- Given a `teaching_assistant` without delegation, when they try to release, then the API returns 403.
- Given unaccepted AI proposals remain, when I release, then those submissions are not released and the count is shown.

### EP-I06 AI-assisted marking and override

#### US-I-022 Request AI-proposed marks
As an **instructor**, I want **the AI to propose marks against my rubric**, so that **I spend my time checking rather than starting from nothing**.\
**Priority:** Must · **Size:** XL · **Release:** R3 · **Dependencies:** US-I-018, US-A-010 · **Use case:** UC-I-08, UC-I-09 · **Trace:** ASM, INS
- Given the flag `instructor.ai_marking` and AI-assisted marking enabled for the cohort, when a submission is submitted, then a proposal with a level, a rationale, and quoted evidence per criterion is stored and `assessment.submission.ai_marked` is emitted.
- Given a proposal, when the learner calls any learner endpoint, then no part of it is returned.
- Given the model call fails, when it is retried 3 times without success, then the submission returns to the manual queue labelled "AI proposal unavailable".

#### US-I-023 Accept, edit, or override a proposed grade
As an **instructor**, I want **to accept the AI's proposal or replace it with a reason**, so that **a human is accountable for every grade**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-022 · **Use case:** UC-I-08, UC-I-09 · **Trace:** ASM
- Given a proposal, when I accept it, then a grade is created that records me as the accountable marker.
- Given I change any criterion level, when I save, then `assessment.grade:override` is required, a reason of at least 10 characters is required, a grade override is stored, `assessment.grade.overridden` is emitted, and the action is audited.
- Given a `teaching_assistant` without override delegation, when they change a proposed level, then the API returns 403.

#### US-I-024 Require approval for large overrides
As a **lead instructor**, I want **large changes to proposed grades approved by a second person when policy requires it**, so that **overrides are controlled**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-023, US-O-008 · **Use case:** UC-I-08, UC-I-09 · **Trace:** ASM, AUTHZ
- Given the organisation's threshold of 10 percentage points, when an override changes the grade by more, then it is held as pending until a `lead_instructor` approves it.
- Given I made the override, when I try to approve it, then it is refused.
- Given a pending override, when grades are released, then that grade is held back.

#### US-I-025 Monitor AI marking agreement
As a **lead instructor**, I want **to see how often humans agree with AI proposals**, so that **I know whether to trust it for this rubric**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-023 · **Use case:** UC-I-08, UC-I-09 · **Trace:** ASM, ANL
- Given 30 or more accepted or overridden proposals for a rubric, when I open quality, then agreement is shown per criterion.
- Given agreement below 70% over the last 30 reviewed proposals for the rubric or for one locale, when it is computed, then AI marking pauses for that rubric or locale and the cohort instructors are notified.
- Given a paused rubric, when I resume it, then the action is audited with a reason.

#### US-I-026 Keep AI marking within data rules
As an **organisation compliance officer**, I want **submissions sent to models only under our rules**, so that **learner work is protected**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-022, US-A-010 · **Use case:** UC-I-08, UC-I-09 · **Trace:** ASM, NFR
- Given a submission, when it is sent for a proposal, then it goes through `ai_gateway` with learner names and emails redacted.
- Given a provider route, when it is used for marking, then it is one whose terms exclude training on inputs, and the route ID is stored with the proposal.
- Given my organisation's policy disables AI marking, when a submission arrives, then no model call is made.

### EP-I07 Progress, risk monitoring, and interventions

#### US-I-027 See cohort progress
As an **instructor**, I want **a grid of learners by plan item and mastery by concept**, so that **I see where the cohort is**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-011 · **Use case:** UC-I-10 · **Trace:** INS, ANL
- Given my cohort, when I open progress, then each learner shows completion per plan item and mastery band per concept in the release.
- Given a personal-account learner, when progress renders, then only concepts in the assigned curriculum appear (ADR 0021).
- Given a cohort of 300 learners, when the grid loads, then the first view renders within 2 seconds at the 95th percentile.

#### US-I-028 See risk signals with evidence
As an **instructor**, I want **learners at risk flagged with the reason**, so that **I can act early**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-I-027 · **Use case:** UC-I-10 · **Trace:** INS, ANL
- Given the daily computation, when a learner has 7 days without activity, 2 missed due dates, a mastery drop of 15 points in 14 days, or engagement below 30% of the cohort median, then a risk signal is stored and `classroom.risk_signal.raised` is emitted.
- Given a risk signal, when I open it, then the evidence (dates, items, values) is shown.
- Given a learner in a cohort I do not teach, when risk signals list, then they are absent.

#### US-I-029 Record an intervention
As an **instructor**, I want **to log what I did about a risk**, so that **colleagues see the history and we can measure what works**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-028 · **Use case:** UC-I-10 · **Trace:** INS
- Given a risk signal, when I record an intervention of type message, meeting, extension, or referral with a follow-up date, then it is stored and linked to the signal.
- Given the follow-up date arrives, when the reminder runs, then I am notified.
- Given an intervention, when the learner opens the Learner App, then instructor notes are not visible to them.

#### US-I-030 Receive a weekly at-risk digest
As an **instructor**, I want **a weekly list of learners at risk**, so that **I plan my week around them**.\
**Priority:** Could · **Size:** S · **Release:** R3 · **Dependencies:** US-I-028, US-P-012 · **Use case:** UC-I-10 · **Trace:** INS, NTF
- Given Monday 08:00 in the cohort timezone, when the digest runs, then I receive new and unresolved signals per cohort.
- Given no signals, when the digest runs, then nothing is sent.
- Given I teach cohorts in two organisations, when digests run, then I receive one per organisation.

### EP-I08 Attendance and engagement

#### US-I-031 Schedule a live session
As an **instructor**, I want **to schedule live sessions in the cohort plan**, so that **learners know when to attend**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-011 · **Use case:** UC-I-11 · **Trace:** INS, NTF
- Given a date, time, duration, and joining link, when I save a live session, then it appears in learners' plans in their timezone.
- Given a live session, when 24 hours and 1 hour remain, then learners receive reminders according to their preferences.
- Given I cancel the session, when it saves, then learners are notified once.

#### US-I-032 Record attendance
As an **instructor**, I want **to record attendance manually, by check-in code, or from activity**, so that **attendance records are complete**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-031 · **Use case:** UC-I-11 · **Trace:** INS
- Given a session, when I show a check-in code, then learners who enter it within 15 minutes are recorded `present` and later entries `late`.
- Given the attendance sheet, when I set a learner to `present`, `late`, `absent`, or `excused`, then it saves with my name and the time.
- Given a required activity window, when it closes, then learners with activity in the window are recorded `present`.

#### US-I-033 Analyse engagement
As an **instructor**, I want **engagement per learner against the cohort**, so that **I notice disengagement before grades fall**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-027 · **Use case:** UC-I-11 · **Trace:** INS, ANL
- Given my cohort, when I open engagement, then each learner shows active days, time on task, mentor sessions, and practice activities for the last 4 weeks against the cohort median.
- Given a learner who has hidden themselves from leaderboards, when engagement renders, then they still appear because engagement is part of the academic record.
- Given engagement data, when I export it, then the export is audited.

#### US-I-034 Export attendance
As a **lead instructor**, I want **to export attendance for a date range**, so that **I can meet reporting duties**.\
**Priority:** Could · **Size:** S · **Release:** R3 · **Dependencies:** US-I-032 · **Use case:** UC-I-11 · **Trace:** INS, RPT
- Given a cohort and date range, when I export, then a CSV lists each learner, session, and status.
- Given a `teaching_assistant`, when they export, then the API returns 403.
- Given an export, when it completes, then it is audited.

### EP-I09 Communication hub

#### US-I-035 Post an announcement
As an **instructor**, I want **to post announcements to a cohort**, so that **everyone gets the same message**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-P-010 · **Use case:** UC-I-12 · **Trace:** MSG, NTF
- Given a cohort, when I post now or schedule an announcement, then members see it in-app and receive it on the channels their preferences allow.
- Given an announcement, when it is posted, then `messaging.announcement.posted` is emitted.
- Given a cohort I do not teach, when I post to it, then the API returns 403.

#### US-I-036 Message a learner
As an **instructor**, I want **private threads with learners in my cohorts**, so that **we can discuss their work**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-035 · **Use case:** UC-I-12 · **Trace:** MSG
- Given a learner in my cohort, when I start a thread, then the learner can reply and other cohort staff can read it.
- Given a learner who is not in any of my cohorts, when I start a thread, then it is refused.
- Given a thread, when the learner leaves the cohort, then it becomes read-only.

#### US-I-037 Run a cohort discussion
As an **instructor**, I want **a discussion space for my cohort**, so that **learners help each other**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-036 · **Use case:** UC-I-12 · **Trace:** MSG
- Given a discussion, when I pin, lock, or remove a post, then the action is recorded with my name.
- Given a learner reports a post, when the report is saved, then cohort staff are notified.
- Given integrity mode is active for an assessment, when policy requires it, then the discussion is read-only until the window closes.

#### US-I-038 Keep messaging safe and retained by policy
As an **organisation compliance officer**, I want **messages screened and retained according to our policy**, so that **communication is safe and lawful**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-036, US-O-030 · **Use case:** UC-I-12 · **Trace:** MSG, NFR
- Given any message, when it is sent, then it passes input screening (BR-11) and rejected content is not delivered.
- Given a retention policy of 2 years, when a message passes it, then it is purged unless under legal hold.
- Given the organisation's audit log, when a staff member deletes a learner's post, then the deletion appears in it.

### EP-I10 Performance analytics

#### US-I-039 See assessment performance
As an **instructor**, I want **score distributions and item statistics**, so that **I can improve my assessments**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-021 · **Use case:** UC-I-13 · **Trace:** ANL, ASM
- Given a released assessment, when I open performance, then I see the score distribution, item difficulty (proportion correct), discrimination index, and average level per rubric criterion.
- Given an item with a discrimination index below 0.1, when statistics render, then it is flagged for review.
- Given fewer than 10 submissions, when statistics would render, then item statistics are hidden.

#### US-I-040 See concept gaps across a cohort
As an **instructor**, I want **the weakest concepts in my cohort**, so that **I reteach what matters**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-I-027 · **Use case:** UC-I-13 · **Trace:** ANL, INS
- Given my cohort, when I open concept gaps, then concepts list by the share of learners in the gap band (BR-08).
- Given a concept, when I select "Assign practice", then a supplementary item is added to the overlay for the learners in the gap band.
- Given a personal-account learner, when gaps are computed, then only concepts in the assigned curriculum count.

#### US-I-041 Compare the cohorts I teach
As a **lead instructor**, I want **cohorts side by side**, so that **I see whether a change in teaching helped**.\
**Priority:** Could · **Size:** S · **Release:** R3 · **Dependencies:** US-I-040 · **Use case:** UC-I-13 · **Trace:** ANL
- Given two or more cohorts in my scope, when I compare them, then completion, average grade, and mastery growth show per cohort.
- Given a cohort outside my scope, when I add it by ID, then the API returns 403.
- Given cohorts on different releases, when compared, then the release version is shown beside each.

#### US-I-042 Export the gradebook
As an **instructor**, I want **to export the gradebook**, so that **I can submit grades to the registry**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-I-021 · **Use case:** UC-I-13 · **Trace:** ASM, RPT
- Given a cohort, when I export, then a CSV and a PDF list each learner, assignment, grade, and weighted total, in the cohort locale.
- Given unreleased grades, when I export, then they are marked "Not released".
- Given an export, when it completes, then it is audited.

---

## 5. Institution App

The Institution App is new in R3. Its users hold `org_owner`, `org_admin`, `campus_admin`, `department_admin`, `org_billing_manager`, `org_report_viewer`, or `org_compliance_officer`. Standards integrations (SCIM, LTI 1.3, OneRoster), white-label domains, and workforce reporting arrive in R4.

### EP-O01 Organisation setup and structure

#### US-O-001 Complete organisation setup
As an **organisation owner**, I want **a setup wizard on first sign-in**, so that **my organisation is ready before instructors arrive**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-A-005 · **Use case:** UC-O-01, UC-O-02 · **Trace:** ORG, TEN
- Given a new organisation, when I complete the wizard, then name, kind, country, default locale, timezone, and contact email are saved and the organisation status becomes `active`.
- Given I skip optional steps (branding, SSO), when I finish, then a checklist on the dashboard lists them.
- Given an `org_admin` who is not `org_owner`, when they try to change the organisation kind, then the API returns 403.

#### US-O-002 Build campuses and departments
As an **organisation admin**, I want **to model our campuses and departments**, so that **permissions and reports follow our structure**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-001 · **Use case:** UC-O-01, UC-O-02 · **Trace:** ORG, TEN
- Given the structure editor, when I add a campus, a faculty under it, and a department under the faculty, then the org unit tree stores them, and a third department level is refused.
- Given I move a department to another campus, when I confirm, then role assignments at that department keep working and reports regroup by the next day.
- Given an org unit with active cohorts, when I try to delete it, then it is refused with the cohort count.

#### US-O-003 Manage members
As an **organisation admin**, I want **to invite, suspend, and remove members**, so that **only the right people have access**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-001 · **Use case:** UC-O-01, UC-O-02 · **Trace:** ORG, TEN, LIC
- Given the members list, when I filter by status (`invited`, `active`, `suspended`, `left`), role, or org unit, then results update.
- Given I suspend a member, when they next call the API in my organisation, then it returns 403 within 60 seconds and their seat stays assigned.
- Given I end a membership, when it is processed, then `tenancy.membership.ended` is emitted and the seat is released.

#### US-O-004 Assign organisation roles at a scope
As an **organisation admin**, I want **to give people roles at the right org unit**, so that **each admin sees only their part of the organisation**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-002, US-P-001 · **Use case:** UC-O-01, UC-O-02 · **Trace:** ORG, AUTHZ
- Given a member, when I assign `department_admin` at a department, then they can manage that department and its cohorts and nothing outside it.
- Given I am `org_admin`, when I try to assign `org_owner`, then it is refused because only an `org_owner` may assign it.
- Given the last `org_owner`, when anyone tries to remove that assignment, then it is refused.

### EP-O02 Instructor and cohort administration

#### US-O-005 Add instructors
As a **department admin**, I want **to add instructors to my department**, so that **they can create and teach cohorts**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-O-004 · **Use case:** UC-O-03, UC-O-04 · **Trace:** ORG, INS
- Given a member or a new email, when I add them as `instructor` or `lead_instructor` at my department, then the assignment is created and they see the Instructor App in their app launcher.
- Given a department outside my scope, when I try to add an instructor there, then the API returns 403.
- Given an instructor added, when the assignment is created, then it is audited.

#### US-O-006 Oversee all cohorts
As a **campus admin**, I want **every cohort in my campus in one list**, so that **I can see what is being taught**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-006 · **Use case:** UC-O-03, UC-O-04 · **Trace:** ORG, INS
- Given my campus, when I open cohorts, then each shows org unit, status, staff, member count, pinned release, and plan progress.
- Given a cohort in another campus, when I request it by ID, then the API returns 403.
- Given a cohort with no instructor, when the list renders, then it is flagged.

#### US-O-007 Reassign cohort staff
As a **department admin**, I want **to move a cohort to another instructor**, so that **teaching continues when someone leaves**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-O-006 · **Use case:** UC-O-03, UC-O-04 · **Trace:** ORG, INS, ASM
- Given a cohort, when I replace its instructor, then the new instructor gets the cohort assignment and the old one loses it within 60 seconds.
- Given unmarked submissions, when staff change, then they move to the new instructor's queue.
- Given the change, when it saves, then it is audited.

#### US-O-008 Set organisation teaching policies
As an **organisation admin**, I want **organisation-wide defaults and limits for teaching**, so that **cohorts follow our academic rules**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-001 · **Use case:** UC-O-03, UC-O-04 · **Trace:** ORG, ASM, PER
- Given the policies page, when I set AI-assisted marking allowed, the override approval threshold, regrade window, late policy, allowed mentor modes, dimension bounds, and leaderboard visibility, then they are saved in `tenancy.org_policies`.
- Given a department policy, when a department admin sets it, then it may tighten but not loosen the organisation's policy.
- Given a policy change, when it saves, then it applies to new requests within 60 seconds and is audited.

### EP-O03 Licences, seats, and billing

#### US-O-009 See my licence and entitlements
As an **organisation billing manager**, I want **the licence terms and seat use**, so that **I know what we pay for and use**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-A-006 · **Use case:** UC-O-05 · **Trace:** LIC
- Given the licence page, when it loads, then it shows plan, term, seats total, assigned, and available, and entitlements.
- Given an `org_report_viewer`, when they open billing, then the API returns 403.
- Given 90% of seats are assigned, when the next seat is assigned, then the billing managers are notified.

#### US-O-010 Assign and reclaim seats
As an **organisation billing manager**, I want **seats assigned automatically and reclaimable**, so that **we do not pay for inactive accounts**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-009 · **Use case:** UC-O-05 · **Trace:** LIC, TEN
- Given `tenancy.membership.activated` for a learner, when it is processed, then a seat is assigned if one is free.
- Given no free seat, when a membership activates, then it activates without learning access and the member sees "Waiting for a seat".
- Given members inactive for 90 days, when I open seats, then they are listed and I can reclaim seats in bulk, and each reclaim is audited.

#### US-O-011 Pay invoices and manage payment methods
As an **organisation billing manager**, I want **invoices and payment methods in one place**, so that **we pay on time**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-009 · **Use case:** UC-O-05 · **Trace:** LIC
- Given invoices, when I open billing, then each shows number, period, amount, status, and a PDF download.
- Given I add a card or set invoice payment, when it saves, then the payment method is stored by Stripe and not in our database.
- Given an `org_admin` without `org_billing_manager`, when they open payment methods, then the API returns 403.

#### US-O-012 Add seats or renew
As an **organisation billing manager**, I want **to add seats or request renewal**, so that **growth is not blocked**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-O-011 · **Use case:** UC-O-05 · **Trace:** LIC
- Given a self-serve plan, when I add 50 seats, then the charge is prorated to the end of the term and `commerce.licence.changed` is emitted.
- Given a contract plan, when I request more seats, then a quote request reaches `finance_admin` and no seats are added until it is approved.
- Given a licence 60 days from its end, when the daily check runs, then the owners and billing managers are notified.

### EP-O04 Branding and domains

#### US-O-013 Brand the apps for our members
As an **organisation admin**, I want **our logo and colours in the apps**, so that **members recognise their institution**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-O-001 · **Use case:** UC-O-06 · **Trace:** ORG
- Given branding settings, when I upload a logo and choose primary and accent colours, then a preview shows the Learner App and Instructor App.
- Given a colour pair with text contrast below 4.5:1, when I save, then it is refused (WCAG 2.2 AA).
- Given a member in my organisation's context, when the Learner App loads, then my branding applies; in the consumer organisation it does not.

#### US-O-014 Customise emails and certificates
As an **organisation admin**, I want **branded email and certificate templates in each locale**, so that **communications look official**.\
**Priority:** Could · **Size:** M · **Release:** R3 · **Dependencies:** US-O-013, US-P-010 · **Use case:** UC-O-06 · **Trace:** ORG, NTF, I18N
- Given a template, when I edit the header, footer, and sign-off for `en`, `fr`, and `es`, then a test send renders each locale.
- Given a locale I did not customise, when a message is sent in it, then the platform default for that locale is used.
- Given a template, when I add an unsupported placeholder, then saving is refused with the placeholder named.

#### US-O-015 Use a custom domain
As an **organisation owner**, I want **the apps on our own domain**, so that **the platform is white-labelled**.\
**Priority:** Should · **Size:** L · **Release:** R4 · **Dependencies:** US-O-013 · **Use case:** UC-O-06 · **Trace:** ORG, NFR
- Given I add `learn.example.edu`, when the CNAME and TXT records verify, then a TLS certificate is issued and the Learner App serves on that host within 30 minutes.
- Given verification fails for 72 hours, when the check runs, then the domain is marked failed and I am notified.
- Given a custom domain, when a member of another organisation signs in there, then they are redirected to the default host.

#### US-O-016 Verify email domains
As an **organisation admin**, I want **to claim our email domain**, so that **people who sign up with it are directed to us**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-O-001 · **Use case:** UC-O-06 · **Trace:** ORG, IAM
- Given I add `example.edu`, when the DNS TXT record verifies, then the domain is stored as verified for my organisation.
- Given a verified domain, when someone signs up with that email domain, then they are offered to join my organisation.
- Given another organisation has verified the same domain, when I add it, then it is refused and `platform_admin` review is offered.

### EP-O05 SSO, SCIM, and LTI

#### US-O-017 Configure SSO
As an **organisation admin**, I want **SAML or OIDC sign-in with our identity provider**, so that **members use their institutional account**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-O-016 · **Use case:** UC-O-07, UC-O-08, UC-O-13, UC-P-01 · **Trace:** IAM, TEN
- Given `tenancy.sso_connection:configure`, when I enter metadata and run the test, then a test sign-in reports the claims received without creating an account.
- Given SSO is enabled, when a new user signs in through it, then a `managed` account and active membership are created just in time.
- Given SSO is enforced for a verified domain, when a member tries a password sign-in, then they are redirected to SSO.

#### US-O-018 Map identity provider groups to roles and cohorts
As an **organisation admin**, I want **identity provider groups mapped to roles and cohorts**, so that **access follows our directory**.\
**Priority:** Should · **Size:** M · **Release:** R4 · **Dependencies:** US-O-017 · **Use case:** UC-O-07, UC-O-08, UC-O-13, UC-P-01 · **Trace:** IAM, AUTHZ
- Given a mapping from group "ml-staff" to `instructor` at a department, when a member of that group signs in, then the assignment is created.
- Given the group is removed from the user, when they next sign in, then the mapped assignment is revoked.
- Given a mapping to `org_owner`, when I try to save it, then it is refused.

#### US-O-019 Provision accounts with SCIM 2.0
As an **organisation admin**, I want **our identity provider to create and deactivate accounts**, so that **leavers lose access promptly**.\
**Priority:** Must · **Size:** L · **Release:** R4 · **Dependencies:** US-O-017 · **Use case:** UC-O-07, UC-O-08, UC-O-13, UC-P-01 · **Trace:** IAM, INT
- Given a SCIM token for my organisation, when the provider calls `/scim/v2/Users`, then users are created, updated, and deactivated in my organisation only.
- Given a deactivation, when it is processed, then the membership ends and sessions are revoked within 5 minutes.
- Given the token used against another organisation's resources, when the call arrives, then it returns 404.

#### US-O-020 Connect our LMS with LTI 1.3 and OneRoster
As an **organisation admin**, I want **AI Mentor to launch from our LMS and return grades**, so that **learners and instructors stay in the tools they use**.\
**Priority:** Must · **Size:** XL · **Release:** R4 · **Dependencies:** US-O-017, US-I-021 · **Use case:** UC-O-07, UC-O-08, UC-O-13, UC-P-01 · **Trace:** INT
- Given a registered LTI 1.3 platform and deployment, when a learner launches a deep-linked course, then they land in the course in the Learner App without a second sign-in.
- Given a released grade for an LTI-linked assignment, when it is released, then it is sent to the LMS line item within 5 minutes.
- Given a nightly OneRoster sync, when it runs, then classes and enrolments create or update cohorts and memberships, and a sync report lists changes and errors.

### EP-O06 Reporting and learning analytics

#### US-O-021 See the organisation dashboard
As an **organisation report viewer**, I want **headline learning metrics for my scope**, so that **I can report to leadership**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-I-027 · **Use case:** UC-O-09, UC-P-04 · **Trace:** RPT, ANL
- Given my scope, when the dashboard loads, then it shows active learners, completion rate, mastery growth, average grade, and seat use, filterable by org unit and date.
- Given a scope at one department, when I filter by another department, then the API returns 403.
- Given data refreshes, when I view the dashboard, then the "data as of" time is shown and is no older than 24 hours.

#### US-O-022 Build and schedule reports
As an **organisation report viewer**, I want **saved reports sent on a schedule**, so that **stakeholders receive them without asking**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-O-021 · **Use case:** UC-O-09, UC-P-04 · **Trace:** RPT, I18N
- Given a report template, when I save filters and a weekly schedule, then it runs and recipients who hold a reporting role in the organisation receive it.
- Given a recipient's locale `fr`, when the report renders, then labels and number formats are French.
- Given a recipient loses their role, when the schedule next runs, then they are removed from it.

#### US-O-023 Respect learner consent in reports
As an **organisation compliance officer**, I want **reports to show personal-account learners only within their consent**, so that **we meet our data agreements**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-L-002, US-O-021 · **Use case:** UC-O-09, UC-P-04 · **Trace:** RPT, TEN
- Given a personal-account member, when a report includes them, then only concepts in curricula the organisation assigned are shown.
- Given that member has left, when a report covers dates after leaving, then their learning record is absent.
- Given an automated test with a personal account in two organisations, when either runs a report, then the other's activity never appears.

#### US-O-024 Export organisation data
As an **organisation admin**, I want **exports of learning and academic data**, so that **we can use it in our own systems**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-O-021 · **Use case:** UC-O-09, UC-P-04 · **Trace:** RPT, INT
- Given an export of enrolments, grades, attendance, or progress, when I request it, then a CSV or XLSX file is produced and available for 7 days.
- Given an `org_report_viewer` at department scope, when they export, then rows outside the department are excluded.
- Given an export, when it completes, then it is audited with row count and filters.

### EP-O07 Workforce development reporting

#### US-O-025 Map job roles to skills
As an **organisation admin in an enterprise**, I want **our job roles mapped to concepts and paths**, so that **learning reports speak our language**.\
**Priority:** Must · **Size:** L · **Release:** R4 · **Dependencies:** US-C-025 · **Use case:** UC-O-10 · **Trace:** RPT, ORG, KG
- Given a job role, when I attach concepts with a target mastery and recommended paths, then it is saved for my organisation only.
- Given a skill framework CSV, when I import it, then each skill maps to a concept or is listed as unmapped.
- Given a member, when their job role is set by SCIM or by an admin, then their role gap is computed the next day.

#### US-O-026 See skills coverage by team
As a **department admin in an enterprise**, I want **a heatmap of skills by team**, so that **I know where to invest in training**.\
**Priority:** Must · **Size:** M · **Release:** R4 · **Dependencies:** US-O-025 · **Use case:** UC-O-10 · **Trace:** RPT, ANL
- Given my department, when I open coverage, then each job role shows the share of members at or above target mastery per concept.
- Given a cell with fewer than 10 people, when the heatmap renders, then the cell is suppressed.
- Given a team outside my scope, when I request it, then the API returns 403.

#### US-O-027 Track mandatory training
As an **organisation admin**, I want **required paths with due dates and completion tracking**, so that **we meet training obligations**.\
**Priority:** Should · **Size:** M · **Release:** R4 · **Dependencies:** US-I-010 · **Use case:** UC-O-10 · **Trace:** RPT, ORG
- Given a required path for a job role, when it is assigned with a due date, then affected members are enrolled and notified.
- Given the compliance view, when it loads, then it shows completion percentage and an overdue list per org unit.
- Given a member overdue by 7 days, when the daily check runs, then they and their department admin are reminded.

#### US-O-028 Report learning investment
As an **organisation owner**, I want **quarterly hours, completions, and credentials by team**, so that **I can justify the investment**.\
**Priority:** Could · **Size:** S · **Release:** R4 · **Dependencies:** US-O-026 · **Use case:** UC-O-10 · **Trace:** RPT
- Given a quarter, when I run the report, then it lists learning hours, completions, credentials issued, and mastery growth per org unit.
- Given the report, when I export it, then it is a PDF in my locale with our branding.
- Given seat cost from the licence, when the report renders, then cost per active learner is shown.

### EP-O08 Compliance and policies

#### US-O-029 Handle data subject requests
As an **organisation compliance officer**, I want **to fulfil access and erasure requests for managed accounts**, so that **we meet GDPR as controller**.\
**Priority:** Must · **Size:** L · **Release:** R3 · **Dependencies:** US-P-017 · **Use case:** UC-O-11, UC-O-12 · **Trace:** ORG, NFR
- Given a request for a managed account, when I log it, then a 30-day deadline is set and shown.
- Given an access request, when I run it, then an export of the account's learning and academic record is produced within 24 hours.
- Given an erasure request, when I confirm it, then `identity.account.erased` is emitted and the account is purged within 30 days except records under legal hold.
- Given a personal-account member, when I start an erasure, then it is refused and I am told the learner controls it through AI Mentor.

#### US-O-030 Set retention policies
As an **organisation compliance officer**, I want **retention periods per data type**, so that **we keep data only as long as we need it**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-O-029 · **Use case:** UC-O-11, UC-O-12 · **Trace:** ORG, NFR
- Given the retention page, when I set periods for submissions, messages, attendance, and audit entries, then values below the platform minimum are refused.
- Given a record past its period, when the nightly job runs, then it is purged and a count is logged.
- Given a legal hold on a member, when the job runs, then that member's records are kept.

#### US-O-031 Review consent records
As an **organisation compliance officer**, I want **the consent each member gave**, so that **I can evidence lawful processing**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-L-002 · **Use case:** UC-O-11, UC-O-12 · **Trace:** ORG, TEN
- Given the consent register, when I filter by consent version, then members who accepted it list with the date.
- Given I publish a new consent version, when members next sign in, then they are asked to accept it.
- Given an export, when I request it, then it is audited.

#### US-O-032 Read the organisation audit log
As an **organisation compliance officer**, I want **the audit log for my organisation**, so that **I can investigate who did what**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-142 · **Use case:** UC-O-11, UC-O-12 · **Trace:** ORG, AUTHZ
- Given `audit.log:read` at organisation scope, when I filter by actor, action, and date, then only entries with my organisation's `tenant_id` are returned.
- Given a platform staff member read my organisation's data, when I open the log, then the entry shows their role and recorded reason.
- Given any entry, when anyone tries to edit or delete it, then it is refused.

---

## 6. Admin App

The Admin App is the operations half of today's `admin/` portal. It acts in the `platform` context, requires the Admin App audience, and requires MFA step-up for sensitive actions. Admin App v1 ships in R2; organisation provisioning arrives with R3.

### EP-A01 Platform user administration

#### US-A-001 Find any person across organisations
As a **platform admin**, I want **to search people across all organisations**, so that **I can support and govern accounts**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-132 · **Use case:** UC-A-02 · **Trace:** ADM, IAM
- Given search by name or email, when results return, then each shows account type, home tenant, memberships, and last active date.
- Given I open a person's tenant-scoped data, when I proceed, then a reason is required and the access is audited and visible in that organisation's audit log.
- Given a token from any app other than the Admin App, when it calls `/api/v1/platform/users`, then it returns 403.

#### US-A-002 Grant and revoke platform roles
As a **platform admin**, I want **to grant platform roles with MFA step-up**, so that **staff have exactly the access they need**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-A-001, US-P-004 · **Use case:** UC-A-02 · **Trace:** ADM, AUTHZ
- Given MFA verified within the last 10 minutes, when I grant `ai_admin` to a person, then the assignment applies on their next request and is audited.
- Given I try to grant a role to myself, when I save, then it is refused.
- Given the last `platform_admin`, when anyone revokes that assignment, then it is refused.

#### US-A-003 Suspend and reinstate an account platform-wide
As a **platform admin**, I want **to suspend an abusive account across all organisations**, so that **the platform stays safe**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-134 · **Use case:** UC-A-02 · **Trace:** ADM, IAM
- Given I suspend with a reason, when the person next calls the API, then every session is refused within 60 seconds.
- Given a suspended account, when leaderboards refresh, then it is hidden from every scope.
- Given I reinstate it, when the person signs in, then access and data are restored and both actions are audited.

#### US-A-004 Act on a support ticket with limited access
As a **support agent**, I want **to see the account facts needed for a ticket**, so that **I can help without broad access**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-A-001 · **Use case:** UC-A-02 · **Trace:** ADM, AUTHZ
- Given a ticket reference, when I open an account, then I see profile, memberships, subscription status, and recent sign-in events, and no conversations, submissions, or grades.
- Given no ticket reference, when I open an account, then the API returns 403.
- Given access granted for a ticket, when 60 minutes pass, then the access window closes.

### EP-A02 Organisation provisioning

#### US-A-005 Create an organisation
As a **platform admin**, I want **to create an organisation and invite its first owner**, so that **a new customer can start**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-P-001 · **Use case:** UC-A-01 · **Trace:** ADM, TEN
- Given name, unique slug, kind, country, and data region, when I create the organisation, then it is stored with status `provisioning` and `tenancy.organisation.created` is emitted.
- Given an owner email, when I invite it, then the invitee becomes `org_owner` on acceptance and the status becomes `active` when setup completes (US-O-001).
- Given the slug `ai-mentor-public` or an existing slug, when I save, then it is refused.

#### US-A-006 Issue and change a licence
As a **finance admin**, I want **to issue licences with seats, term, and entitlements**, so that **organisations get what they bought**.\
**Priority:** Must · **Size:** M · **Release:** R3 · **Dependencies:** US-A-005 · **Use case:** UC-A-01 · **Trace:** LIC, ADM
- Given an organisation, when I issue a licence with plan, seat count, start and end dates, and entitlements, then `commerce.licence.changed` is emitted and entitlements apply within 60 seconds.
- Given I reduce seats below the number assigned, when I save, then I must choose to block new assignments or reclaim the most inactive seats.
- Given a `platform_operator`, when they try to change a licence, then the API returns 403.

#### US-A-007 Suspend or close an organisation
As a **platform admin**, I want **to suspend or close an organisation**, so that **non-payment and contract ends are handled cleanly**.\
**Priority:** Should · **Size:** L · **Release:** R3 · **Dependencies:** US-A-006 · **Use case:** UC-A-01 · **Trace:** ADM, TEN, NFR
- Given I suspend an organisation with a reason, when managed accounts sign in, then they see a suspension notice; personal-account members keep their learning record in the consumer organisation.
- Given I close an organisation, when it is confirmed with MFA step-up, then owners get a 30-day export window before data is purged.
- Given a closure, when the purge runs, then `tenancy.organisation.closed` is emitted and the purge is audited.

#### US-A-008 Enable an organisation workspace
As a **platform admin**, I want **to enable a private content workspace for an organisation**, so that **it can author and derive its own courses**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-A-006, US-C-004 · **Use case:** UC-A-01 · **Trace:** ADM, CST
- Given a licence with the workspace entitlement, when I enable it, then an `org` workspace is created for the organisation.
- Given the workspace, when the `org_admin` assigns `content_author` there, then the author can open Content Studio scoped to that workspace only.
- Given a licence without the entitlement, when I try to enable it, then it is refused.

### EP-A03 AI services and model management

#### US-A-009 Register models
As an **AI admin**, I want **a registry of the models we may use**, so that **routing and cost are governed**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-137 · **Use case:** UC-A-03 · **Trace:** ADM, TUT
- Given a model, when I register provider, model name, region, context window, capabilities, price per million tokens in and out, and data terms, then it is stored in `platform.model_registry` with status `candidate`.
- Given a test call fails, when I try to activate the model, then it stays `candidate` with the error.
- Given API keys, when they are configured, then they live in the secrets manager only (US-137).

#### US-A-010 Route tasks to models with failover
As an **AI admin**, I want **per-task routes with fallbacks**, so that **features stay up and costs stay controlled**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-A-009 · **Use case:** UC-A-03 · **Trace:** ADM, TUT, ASM
- Given `ai.model_route:edit`, when I set ordered models for tutor, quiz generation, marking, content generation, embeddings, and translation, then the gateway uses that order.
- Given the first model times out, when a request runs, then the next model is tried in the same request and the fallback is traced.
- Given an organisation with an EU data region, when a route would send its data to a model outside that region, then that model is skipped.

#### US-A-011 Release prompts and policies through evaluation gates
As an **AI admin**, I want **prompt and policy changes released only after evaluation**, so that **quality and safety do not regress**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-A-010 · **Use case:** UC-A-03 · **Trace:** ADM, TUT
- Given a prompt release candidate, when its evaluation runs, then it must meet the thresholds set for that agent (for example groundedness at least 0.85 and zero critical safety failures on the golden set) before promotion.
- Given a promoted release, when I roll back, then the previous release serves new requests within 60 seconds.
- Given each release, when it is promoted, then it is audited with the evaluation report.

#### US-A-012 Control AI cost by organisation
As an **AI admin**, I want **monthly AI budgets per organisation**, so that **spend matches the licence**.\
**Priority:** Should · **Size:** M · **Release:** R3 · **Dependencies:** US-138 · **Use case:** UC-A-03 · **Trace:** ADM, LIC
- Given a budget, when spend reaches 80% and 100%, then the AI admin and the organisation's billing managers are alerted.
- Given 100% is reached, when the licence says "degrade", then requests route to the cheapest active model; when it says "block", then new AI requests return 429 with a clear message.
- Given the cost view, when I open it, then daily cost by organisation, task, and model is shown.

### EP-A04 Feature flags and settings

#### US-A-013 Create and roll out a feature flag
As a **platform operator**, I want **flags with targeting rules**, so that **features roll out safely**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** None · **Use case:** UC-A-04 · **Trace:** PLT, ADM
- Given `platform.feature_flag:edit`, when I create `instructor.ai_marking` with rules by app, organisation, and percentage, then evaluation follows the rules in order.
- Given a key that does not match `<app_or_context>.<feature>`, when I save, then it is refused.
- Given a change, when it saves, then it is audited with before and after.

#### US-A-014 Switch a feature off quickly
As a **platform operator**, I want **a kill switch for any flag**, so that **I can stop a bad release in an incident**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-A-013 · **Use case:** UC-A-04 · **Trace:** PLT
- Given an enabled flag, when I turn it off globally, then every API instance evaluates it as off within 60 seconds.
- Given the flag service is unreachable, when a flag is evaluated, then its declared default is used.
- Given a kill switch, when it is used, then an incident note is required.

#### US-A-015 Edit platform settings
As a **platform operator**, I want **validated platform settings**, so that **configuration changes do not break the platform**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** None · **Use case:** UC-A-04 · **Trace:** PLT
- Given a setting such as the daily XP cap, when I enter a value outside its schema, then it is refused.
- Given a setting marked sensitive, when I change it, then MFA step-up and a second `platform_operator` approval are required.
- Given any change, when it saves, then it is audited.

#### US-A-016 Clean up stale flags
As a **platform operator**, I want **to see flags that no longer vary**, so that **code stays simple**.\
**Priority:** Could · **Size:** S · **Release:** R2 · **Dependencies:** US-A-013 · **Use case:** UC-A-04 · **Trace:** PLT
- Given flags at 100% or 0% for 90 days, when I open flag health, then they are listed with their owner.
- Given a flag with no evaluations for 30 days, when I open flag health, then it is marked unused.
- Given I archive a flag, when code still evaluates it, then the default is returned and a warning is logged.

### EP-A05 Audit and security monitoring

#### US-A-017 Search the platform audit log
As a **security auditor**, I want **to search all audit entries**, so that **I can investigate incidents**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-142 · **Use case:** UC-A-05, UC-A-06, UC-A-10 · **Trace:** ADM, AUTHZ
- Given `audit.log:read` at platform scope, when I filter by actor, tenant, action, target, and date, then results return within 3 seconds for 90 days of data.
- Given `security_auditor`, when I try any write action in the Admin App, then the API returns 403.
- Given an export, when I request it, then it is itself audited.

#### US-A-018 Monitor security signals
As a **security auditor**, I want **alerts on suspicious patterns**, so that **attacks are caught early**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-140 · **Use case:** UC-A-05, UC-A-06, UC-A-10 · **Trace:** ADM, NFR
- Given more than 20 cross-tenant denials for one account in a minute, when monitoring runs, then an alert fires.
- Given 10 failed sign-ins for one account in 10 minutes, when it happens, then an alert fires and the account is rate-limited.
- Given the security dashboard, when it loads, then safety events, denials, rate-limit hits, and webhook signature failures show by hour.

#### US-A-019 Review authorization decisions
As a **security auditor**, I want **the authorization decision log**, so that **I can verify the policy engine works**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-P-001 · **Use case:** UC-A-05, UC-A-06, UC-A-10 · **Trace:** AUTHZ
- Given the decision log, when I filter by permission and outcome, then each entry shows subject, permission, resource, scope, matched policy, and outcome.
- Given a denial, when I open it, then the failing condition (scope, attribute, or explicit deny) is named.
- Given decision log retention of 90 days, when an entry passes it, then it is purged.

#### US-A-020 Record platform access to tenant data
As a **platform admin**, I want **every read of tenant data from the platform context to require a reason**, so that **organisations can trust our staff access**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-A-001 · **Use case:** UC-A-05, UC-A-06, UC-A-10 · **Trace:** TEN, AUTHZ
- Given a platform role, when I open a tenant's cohorts, submissions, or reports, then a reason of at least 10 characters is required.
- Given the access, when it is granted, then an audit entry is written with the tenant's `tenant_id`.
- Given a request without a reason, when it reaches the API, then it returns 403.

### EP-A06 Subscriptions and global reporting

#### US-A-021 Manage consumer subscriptions
As a **finance admin**, I want **to view and correct consumer subscriptions**, so that **billing issues are resolved**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-103 · **Use case:** UC-A-07, UC-A-08 · **Trace:** LIC, ADM
- Given a learner, when I open their subscription, then plan, status, period, and Stripe event history show.
- Given a Stripe event delivered twice, when it is processed, then the second delivery changes nothing.
- Given I change a plan manually, when I save, then `commerce.subscription.changed` is emitted and the change is audited.

#### US-A-022 Refund and credit
As a **finance admin**, I want **to issue refunds and credits with a reason**, so that **customers are treated fairly**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-A-021 · **Use case:** UC-A-07, UC-A-08 · **Trace:** LIC
- Given a payment, when I refund part or all with a reason, then the refund is made through Stripe and audited.
- Given a refund above the configured limit, when I submit it, then a second `finance_admin` must approve.
- Given a `support_agent`, when they try to refund, then the API returns 403.

#### US-A-023 See global platform metrics
As a **platform admin**, I want **platform-wide metrics**, so that **leadership sees how the business is doing**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-135 · **Use case:** UC-A-07, UC-A-08 · **Trace:** ADM, ANL, RPT
- Given the global dashboard, when it loads, then it shows active learners by app, organisations by kind, retention, recurring revenue, and AI cost.
- Given a filter by organisation kind or country, when I apply it, then all metrics update.
- Given the dashboard, when it renders, then it shows aggregates only and no individual learner.

#### US-A-024 Publish de-identified benchmarks
As a **platform admin**, I want **benchmarks organisations can compare against**, so that **they see how they perform without exposing others**.\
**Priority:** Could · **Size:** M · **Release:** R4 · **Dependencies:** US-O-021 · **Use case:** UC-A-07, UC-A-08 · **Trace:** ANL, RPT, TEN
- Given a benchmark, when it is computed, then each cell includes at least 5 organisations and 10 learners or is suppressed.
- Given an organisation's dashboard, when it shows a benchmark, then no other organisation's name or identifier is returned.
- Given a benchmark is published, when it is released, then it is audited.

### EP-A07 Content and knowledge governance oversight

#### US-A-025 Work the moderation queue
As a **platform admin**, I want **unsafe tutor replies and reported content in one queue**, so that **harm is handled fast**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-035, US-130 · **Use case:** UC-A-09 · **Trace:** ADM, TUT
- Given `tutor.message.flagged` with reason unsafe, when it is processed, then a queue item appears within 1 minute with the redacted message and context.
- Given an item, when I resolve it as warn, suspend, or dismiss, then the action is audited and linked content can be sent to Content Studio as a fix request.
- Given an item older than 24 hours, when the queue renders, then it is marked overdue.

#### US-A-026 See content pipeline health
As a **platform admin**, I want **counts of content by state and ingestion failures across workspaces**, so that **content operations do not stall**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-C-033 · **Use case:** UC-A-09 · **Trace:** ADM, CST
- Given the pipeline view, when it loads, then items per state (`draft`, `in_review`, `approved`, `published`, `archived`) show per workspace.
- Given items in `in_review` for more than 5 working days, when the view renders, then they are listed.
- Given failed ingestions, when the view renders, then each shows the error and a link to retry in Content Studio.

#### US-A-027 Take down content for legal reasons
As a **platform admin**, I want **to withdraw content everywhere when rights or law require it**, so that **we meet legal obligations**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-037 · **Use case:** UC-A-09 · **Trace:** ADM, CST, KM
- Given a takedown with a legal reason and MFA step-up, when I confirm it, then the asset leaves retrieval and learner views within 5 minutes, including releases pinned by cohorts.
- Given affected cohorts, when the takedown completes, then their instructors are notified with the affected items.
- Given a takedown, when it is recorded, then it is audited and can be lifted only by a `platform_admin`.

#### US-A-028 Oversee knowledge governance quality
As a **platform admin**, I want **knowledge quality indicators**, so that **the knowledge base stays trustworthy**.\
**Priority:** Could · **Size:** S · **Release:** R2 · **Dependencies:** US-C-024 · **Use case:** UC-A-09 · **Trace:** ADM, KM, KG
- Given the governance view, when it loads, then it shows concepts with no lesson, lessons with no concept, assets without rights metadata, and stale assets not reviewed in 12 months.
- Given an indicator, when I select it, then the list opens in Content Studio for the `knowledge_steward`.
- Given the view, when a `support_agent` opens it, then the API returns 403.

---

## 7. Content Studio

Content Studio is the content half of today's `admin/` portal. It splits out in R1 with the v1 knowledge portal stories (US-106 to US-131) and gains builders, releases, workflow, and localisation in R2. Every story acts in one workspace: `master` or an organisation's `org` workspace.

### EP-C01 Knowledge repository and asset management

#### US-C-001 Upload any of the thirteen asset kinds
As a **content author**, I want **to upload every kind of knowledge asset**, so that **all source material is governed in one place**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-106 · **Use case:** UC-C-01 · **Trace:** CST, KM
- Given the upload form, when I choose a kind, then the 13 kinds are offered: PDF, book, paper, lecture notes, slides, video, dataset, repository, external link, image, audio, assessment, and lesson content.
- Given a document over 50 MB or a video over 2 GB, when I upload it, then it is refused before transfer completes.
- Given an upload, when it is saved, then it is a `draft` asset version in my workspace with my name and time.

#### US-C-002 Record rights and licence terms
As a **content author**, I want **rights recorded for every asset**, so that **we only use material we may use**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-C-001 · **Use case:** UC-C-01 · **Trace:** KM, NFR
- Given an asset, when I submit it for review, then rights holder, licence (for example CC BY 4.0), and allowed uses (display, retrieval, derivative generation) are required.
- Given an asset whose licence forbids derivatives, when AI generation lists sources, then it is excluded.
- Given rights metadata, when it changes on a published asset, then a new version is required.

#### US-C-003 Ingest published asset versions into retrieval
As a **content publisher**, I want **published asset versions to reach the tutor automatically**, so that **learners get current material**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-108 · **Use case:** UC-C-01 · **Trace:** KM, EVT
- Given `knowledge.asset_version.published`, when retrieval consumes it, then chunks and embeddings are created with lineage to the asset version within 10 minutes.
- Given a newer version is published, when ingestion completes, then the previous version's vectors stop being returned.
- Given ingestion fails, when it is retried 3 times without success, then the asset shows "Ingestion failed" with the error (US-109).

#### US-C-004 Keep workspaces separate
As an **organisation content author**, I want **our workspace private to our organisation**, so that **our material is not exposed**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-P-001 · **Use case:** UC-C-01 · **Trace:** CST, TEN
- Given an asset in organisation A's workspace, when an author in `master` or organisation B requests it by ID, then the API returns 404.
- Given retrieval for a learner in organisation B, when it runs, then organisation A's private chunks are never returned.
- Given an automated test seeding one asset per workspace, when it runs for each workspace role, then each sees only its own workspace and `master` published content.

### EP-C02 Lesson builder

#### US-C-005 Create a lesson with a primary concept and objectives
As a **content author**, I want **to start a lesson from its concept and objectives**, so that **every lesson teaches something measurable**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-118, US-C-025 · **Use case:** UC-C-02 · **Trace:** CST
- Given a new lesson, when I save it, then a primary concept, 1 to 5 objectives, estimated minutes, and level are required.
- Given secondary concepts, when I add them, then they are stored with the lesson and appear in the knowledge graph view.
- Given a lesson, when it is saved, then its state is `draft`.

#### US-C-006 Write lesson bodies per locale and approach
As a **content author**, I want **variants of a lesson body by locale and approach**, so that **the Learner App can match each learner's settings**.\
**Priority:** Should · **Size:** L · **Release:** R2 · **Dependencies:** US-C-005 · **Use case:** UC-C-02 · **Trace:** CST, PER, I18N
- Given a lesson, when I add a body, then I choose a locale and an `approach` value, and an `en` Balanced body is required before review.
- Given a learner with `approach` Mathematical and no Mathematical body, when the lesson renders, then the Balanced body is used.
- Given a missing locale body, when a learner opens the lesson, then the `en` body is shown with a notice.

#### US-C-007 Embed checks, code, and media
As a **content author**, I want **checks, runnable code, and media inside a lesson**, so that **learners practise as they read**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-C-005 · **Use case:** UC-C-02 · **Trace:** CST
- Given the block editor, when I insert a check, code cell, image, video, equation, or callout, then it renders in preview as in the Learner App.
- Given a check, when I link it to an item bank item, then completing it feeds mastery for the item's concept.
- Given an image without alternative text, when I submit for review, then submission is refused with the block named.

#### US-C-008 Preview a lesson as a learner
As a **content author**, I want **to preview with chosen learner settings**, so that **I see what each learner sees**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-C-006 · **Use case:** UC-C-02 · **Trace:** CST
- Given preview, when I choose locale, the five dimensions, and device width, then the lesson renders with those settings.
- Given preview, when it runs, then no progress, XP, or analytics events are recorded.
- Given a preview link, when someone without a workspace role opens it, then it returns 404.

### EP-C03 Course, module, and curriculum builder

#### US-C-009 Assemble modules
As a **content author**, I want **to group lessons and checks into modules**, so that **courses have a clear structure**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-005 · **Use case:** UC-C-03 · **Trace:** CST
- Given a module, when I add and reorder lessons and checks, then the order saves immediately.
- Given a lesson used in two modules, when it is edited, then both modules reference the same lesson.
- Given a module, when it is saved, then its estimated minutes are the sum of its items.

#### US-C-010 Build a course
As a **content author**, I want **to define a course with outcomes, prerequisites, and assessments**, so that **institutions can assign it**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-C-009 · **Use case:** UC-C-03 · **Trace:** CST, ASM
- Given a course, when I add modules, outcomes, prerequisite concepts, and assessments, then each outcome links to at least one concept.
- Given an assessment from the item bank, when I attach it to the course, then it is included in the next release.
- Given a course, when I save it, then its state is `draft`.

#### US-C-011 Validate course structure
As a **content reviewer**, I want **automatic structure checks**, so that **I review quality, not completeness**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-010 · **Use case:** UC-C-03 · **Trace:** CST, KG
- Given a course, when validation runs, then it fails if a lesson's prerequisite concept is first taught later in the course, if an outcome has no assessment, or if any item is not `approved` or `published`.
- Given validation fails, when I open the report, then each problem links to the item.
- Given validation passes, when the author submits, then the report is attached to the review.

#### US-C-012 Derive a course in an organisation workspace
As an **organisation content author**, I want **to copy a master course and edit it while tracking the original**, so that **we tailor it and still receive updates**.\
**Priority:** Should · **Size:** L · **Release:** R3 · **Dependencies:** US-A-008, US-C-030 · **Use case:** UC-C-03 · **Trace:** CST, TEN
- Given a `master` release in our licence, when I derive it, then a `draft` copy is created in our workspace with a link to the upstream release.
- Given a new upstream release, when it is published, then I see a change list and can accept or reject each change.
- Given the derived course, when it is published, then it is visible only to our organisation.

### EP-C04 Learning path builder

#### US-C-013 Build a path toward a goal
As a **content author**, I want **to sequence courses, modules, and projects toward a goal or role**, so that **learners follow a coherent journey**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-116, US-C-010 · **Use case:** UC-C-04 · **Trace:** CST
- Given a path, when I add courses, standalone modules, and projects, then each is referenced by release.
- Given a target role, when I link it, then the path appears in career planning for that role (US-L-030).
- Given a path, when it is saved, then its state is `draft`.

#### US-C-014 Order a path and check prerequisites
As a **content author**, I want **drag-and-drop ordering with prerequisite checks**, so that **the order makes sense**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-117, US-C-013 · **Use case:** UC-C-04 · **Trace:** CST, KG
- Given I drag a course before one it depends on, when I drop it, then a warning names the prerequisite concept.
- Given a keyboard user, when they move an item with arrow keys and space, then the order changes the same way.
- Given a reorder, when it saves, then it is recorded in the version history.

#### US-C-015 Define path completion and credentials
As a **content author**, I want **completion rules and a credential for a path**, so that **learners earn recognition**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-C-013 · **Use case:** UC-C-04 · **Trace:** CST, GAM
- Given completion rules, when I set required items and a minimum mastery, then completion is evaluated against them.
- Given a credential, when a learner completes the path, then an Open Badges 3.0 credential is issued.
- Given a rule change, when it is published in a new release, then learners on the old release keep the old rule.

#### US-C-016 Publish a path release pinned to course releases
As a **content publisher**, I want **path releases to pin exact course releases**, so that **a path does not change underneath learners**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-013, US-C-036 · **Use case:** UC-C-04 · **Trace:** CST
- Given a path, when I publish it, then each referenced course is pinned to a published release version.
- Given a referenced course release is archived, when I open the path, then it is flagged.
- Given a path release, when it is published, then `content.release.published` is emitted.

### EP-C05 Quiz builder and item bank

#### US-C-017 Author items for the item bank
As a **content author**, I want **to write assessment items linked to concepts**, so that **quizzes and assessments measure mastery**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-C-025 · **Use case:** UC-C-05 · **Trace:** ASM, CST
- Given the item editor, when I create multiple choice, multiple select, true/false, fill in the blank, numeric, short answer, written response, or coding items, then each requires a concept, difficulty, answer key or rubric, and rationale.
- Given a coding item, when I save it, then its tests must pass against the reference solution in the sandbox.
- Given an item, when it is saved, then it follows the same workflow states as other content.

#### US-C-018 Build quizzes and item pools
As a **content author**, I want **to build quizzes from items and pools**, so that **courses ship with ready assessments**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-017 · **Use case:** UC-C-05 · **Trace:** ASM, CST
- Given a quiz, when I add fixed items and draw rules, then the preview draws a valid set.
- Given a pool smaller than its draw count, when I save, then it is refused.
- Given a quiz, when it is released with a course, then instructors can use it in assignments (US-I-014).

#### US-C-019 Calibrate item difficulty from data
As a **knowledge steward**, I want **difficulty suggestions from real attempts**, so that **items are labelled accurately**.\
**Priority:** Could · **Size:** M · **Release:** R3 · **Dependencies:** US-C-017 · **Use case:** UC-C-05 · **Trace:** ASM, ANL
- Given 50 or more attempts, when calibration runs weekly, then a difficulty change is suggested if the proportion correct falls outside the labelled band.
- Given a suggestion, when I accept it, then a new item version is created.
- Given attempts from organisation-authored assessments, when calibration runs, then only attempts on `master` items count toward `master` calibration.

#### US-C-020 Freeze and retire items
As a **content publisher**, I want **items in live graded assessments frozen**, so that **an edit cannot change a test in progress**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-I-016 · **Use case:** UC-C-05 · **Trace:** ASM, AUTHZ
- Given an item used in an assessment whose window is open, when anyone tries to edit it, then an explicit deny policy refuses the edit.
- Given a retired item, when instructors search the bank, then it is not returned and existing uses keep working.
- Given an item exposed in a reported integrity breach, when I retire it, then the retirement is audited.

### EP-C06 Taxonomy and metadata

#### US-C-021 Manage the taxonomy
As a **knowledge steward**, I want **to maintain the taxonomy**, so that **content is classified consistently**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-112 · **Use case:** UC-C-06 · **Trace:** KM
- Given the taxonomy, when I add, rename, merge, or deprecate a term, then tagged items follow merges and keep deprecated tags with a warning.
- Given a term label, when I edit it, then `en`, `fr`, and `es` labels can be set.
- Given a `content_author`, when they try to edit the taxonomy, then the API returns 403.

#### US-C-022 Define the metadata schema
As a **knowledge steward**, I want **required and optional fields per content type**, so that **metadata is complete and searchable**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-C-021 · **Use case:** UC-C-06 · **Trace:** KM
- Given a content type, when I mark a field required, then submission for review fails without it.
- Given a controlled vocabulary field, when an author types a value not in it, then it is refused.
- Given a schema change, when it saves, then existing items are not invalidated until they are next edited.

#### US-C-023 Tag in bulk with suggestions
As a **content author**, I want **suggested tags I can confirm in bulk**, so that **tagging is fast and accurate**.\
**Priority:** Could · **Size:** M · **Release:** R2 · **Dependencies:** US-C-021 · **Use case:** UC-C-06 · **Trace:** KM, CST
- Given selected items, when I request suggestions, then each tag shows a confidence from 0 to 1.
- Given I confirm suggestions, when they save, then they are recorded as human-confirmed.
- Given unconfirmed suggestions, when the item is submitted, then they are not applied.

#### US-C-024 Report metadata quality
As a **knowledge steward**, I want **metadata completeness by workspace**, so that **I know where to focus**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-C-022 · **Use case:** UC-C-06 · **Trace:** KM
- Given the quality report, when it loads, then it shows the share of items with all required fields per content type.
- Given a filter by author, when I apply it, then counts update.
- Given an `org` workspace steward, when they open the report, then only their workspace is included.

### EP-C07 Knowledge graph management

#### US-C-025 Edit concepts and relations
As a **knowledge steward**, I want **to edit concepts and typed relations**, so that **the graph reflects how the field fits together**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-114 · **Use case:** UC-C-07 · **Trace:** KG
- Given `knowledge.concept_relation:edit`, when I add a relation of type `prerequisite_of`, `builds_on`, `related_to`, `part_of`, `applies_to`, or `contrasts_with` with a weight from 0.0 to 1.0, then it saves and `knowledge.concept_relation.changed` is emitted.
- Given a concept, when I edit its slug, then the change is refused once any published lesson uses it.
- Given a `content_author`, when they try to edit a relation, then the API returns 403 and they are offered to propose it (US-C-027).

#### US-C-026 Keep prerequisite edges acyclic
As a **knowledge steward**, I want **cycles in prerequisites refused**, so that **sequencing always has a valid order**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-C-025 · **Use case:** UC-C-07 · **Trace:** KG
- Given a new `prerequisite_of` edge that would create a cycle, when I save, then it is refused and the cycle path is shown.
- Given a bulk import of relations, when any edge creates a cycle, then the whole import is refused.
- Given other relation types, when they form cycles, then they are allowed.

#### US-C-027 Review proposed relations
As a **knowledge steward**, I want **a queue of relations proposed by authors and AI**, so that **the graph grows with oversight**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-115, US-C-025 · **Use case:** UC-C-07 · **Trace:** KG
- Given a proposal, when I open it, then I see the proposer (person or model), evidence, and the affected concepts.
- Given I accept it, when it saves, then it becomes a relation and the proposer is notified.
- Given an AI proposal, when it is listed, then it is labelled "AI-proposed".

#### US-C-028 See impact before changing the graph
As a **knowledge steward**, I want **the impact of a graph change before I save it**, so that **I do not disrupt learners unexpectedly**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-C-025 · **Use case:** UC-C-07 · **Trace:** KG, PER
- Given a change to a prerequisite edge, when I preview it, then the number of affected lessons, courses, and active learners shows.
- Given more than 1,000 affected learners, when I save, then a second `knowledge_steward` must approve.
- Given a saved change, when personalisation consumes the event, then recommendations use it within 15 minutes.

### EP-C08 Versioning and releases

#### US-C-029 Version every content item
As a **content author**, I want **every change kept as a version**, so that **history is complete**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-127 · **Use case:** UC-C-09 · **Trace:** CST
- Given an edit to a lesson, module, course, path, or item, when it saves, then a version with number, editor, time, and change note is stored.
- Given a version, when anyone tries to delete it, then it is refused.
- Given versions, when I compare two, then additions and deletions show for content and metadata (US-128).

#### US-C-030 Cut a semantic-versioned release
As a **content publisher**, I want **releases numbered by the size of the change**, so that **instructors know what an update means**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-029 · **Use case:** UC-C-09 · **Trace:** CST
- Given changes since the last release, when I prepare a release, then MAJOR is suggested if lessons or outcomes were removed, MINOR if items were added, and PATCH for corrections only.
- Given a release, when it is created, then its content is immutable.
- Given release notes, when I publish, then they are required in `en`.

#### US-C-031 Compare releases
As an **instructor or content reviewer**, I want **a diff between two releases**, so that **I can judge an update**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-C-030 · **Use case:** UC-C-09 · **Trace:** CST, INS
- Given two releases, when I compare them, then added, removed, and changed lessons, items, and outcomes are listed.
- Given a changed lesson, when I open it, then a text diff shows.
- Given an instructor, when they compare, then only releases their organisation can access are offered.

#### US-C-032 Restore a version or roll back a release
As a **content publisher**, I want **to recover from a bad change**, so that **learners get correct content quickly**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-129, US-C-030 · **Use case:** UC-C-09 · **Trace:** CST
- Given an older version, when I restore it, then a new `draft` version is created with its content.
- Given a bad release, when I roll back, then a new PATCH release with the earlier content is published and pinned cohorts are notified.
- Given a rollback, when it completes, then it is audited.

### EP-C09 Review and publishing workflow

#### US-C-033 Submit content for review
As a **content author**, I want **to submit my draft for review**, so that **it can be checked and published**.\
**Priority:** Must · **Size:** S · **Release:** R1 · **Dependencies:** US-121 · **Use case:** UC-C-08, UC-C-09, UC-C-12 · **Trace:** CST
- Given a `draft`, when I submit, then it becomes `in_review`, `content.item.state_changed` is emitted, and reviewers in the workspace are notified.
- Given missing required metadata or a failed validation, when I submit, then the missing items are named.
- Given an item `in_review`, when I edit it, then I must first withdraw it to `draft`.

#### US-C-034 Review and request changes
As a **content reviewer**, I want **to approve or request changes with anchored comments**, so that **quality stays high**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-C-033 · **Use case:** UC-C-08, UC-C-09, UC-C-12 · **Trace:** CST
- Given an item `in_review`, when I approve it, then it becomes `approved`.
- Given I request changes, when I confirm, then it becomes `changes_requested`, returns to `draft` with my comments, and the author is notified.
- Given a reviewer in `master`, when they open an item in an `org` workspace, then the API returns 404.

#### US-C-035 Enforce the two-person rule
As a **content publisher**, I want **authors unable to approve their own work**, so that **every item has a second reviewer**.\
**Priority:** Must · **Size:** S · **Release:** R1 · **Dependencies:** US-C-034 · **Use case:** UC-C-08, UC-C-09, UC-C-12 · **Trace:** CST, AUTHZ
- Given I am the author of an item or of any version under review, when I try to approve it, then the policy engine denies it.
- Given a `platform_admin` emergency override, when it is used, then MFA step-up and a reason are required and it is audited.
- Given an AI-generated draft, when it is reviewed, then the person who requested generation counts as its author.

#### US-C-036 Publish or schedule a release
As a **content publisher**, I want **to publish approved content now or at a set time**, so that **learners receive it when it is ready**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-C-034 · **Use case:** UC-C-08, UC-C-09, UC-C-12 · **Trace:** CST, EVT
- Given `content.course:publish` and an `approved` course, when I publish, then a release is created, `content.release.published` is emitted, and it is visible to entitled learners within 1 minute.
- Given a scheduled time, when it arrives, then the release publishes automatically.
- Given a `content_author` or `content_reviewer`, when they try to publish, then the API returns 403.

#### US-C-037 Archive a release safely
As a **content publisher**, I want **to archive a release without stranding cohorts**, so that **outdated content retires cleanly**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-036 · **Use case:** UC-C-08, UC-C-09, UC-C-12 · **Trace:** CST, INS
- Given a published release, when I archive it, then new enrolments are blocked and `content.release.archived` is emitted.
- Given cohorts pinned to it, when it is archived, then they keep access until their end date and their instructors are notified.
- Given learners who completed its lessons, when they view progress, then completions and XP remain (US-126).

### EP-C10 AI content generation

#### US-C-038 Generate drafts from sources
As a **content author**, I want **lessons, items, flashcards, and summaries generated from chosen assets**, so that **I build material faster**.\
**Priority:** Should · **Size:** L · **Release:** R2 · **Dependencies:** US-119, US-C-002 · **Use case:** UC-C-10 · **Trace:** CST, KM
- Given selected published assets, when I request generation with type, level, locale, and count, then output uses only those assets' chunks and cites the sections used.
- Given generated output, when it is saved, then it is `draft` and labelled "AI-generated" permanently (US-120).
- Given partial failure, when results show, then completed items are kept and the rest can be retried.

#### US-C-039 Generate translation drafts
As a **localisation editor**, I want **machine translation drafts**, so that **I edit rather than translate from nothing**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-C-042 · **Use case:** UC-C-10 · **Trace:** I18N, CST
- Given a translation job, when I request drafts for `fr`, then each segment is pre-filled and marked machine-translated.
- Given translation memory matches, when drafts are produced, then exact matches are used before machine translation.
- Given a draft, when it is saved, then its `translation_status` is not `approved`.

#### US-C-040 Check generated content for grounding
As a **content reviewer**, I want **grounding and quality checks on generated content**, so that **I catch errors before learners do**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-C-038 · **Use case:** UC-C-10 · **Trace:** CST, TUT
- Given a generated item, when checks run, then a groundedness score from 0 to 1 is attached and items below 0.7 are flagged "Ungrounded".
- Given a generated item with an answer key, when checks run, then the key is verified against the cited source and mismatches are flagged.
- Given flags, when I review, then flagged items cannot be approved until each flag is resolved.

#### US-C-041 Respect rights and cost limits when generating
As a **knowledge steward**, I want **generation limited to permitted sources and budgets**, so that **we stay lawful and within cost**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-C-002, US-A-012 · **Use case:** UC-C-10 · **Trace:** KM, CST
- Given an asset whose allowed uses exclude derivative generation, when I select it, then it cannot be used.
- Given the workspace's monthly generation budget is spent, when I request generation, then it is refused with the reset date.
- Given a generation request, when it runs, then model, tokens, and cost are traced against the workspace.

### EP-C11 Localisation workflow

#### US-C-042 Request translations for a release
As a **content publisher**, I want **translation jobs per locale for a release**, so that **content reaches French and Spanish learners**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-092, US-C-030 · **Use case:** UC-C-11 · **Trace:** I18N, CST
- Given a release, when I request `fr` and `es`, then one job per locale lists every translatable segment.
- Given an existing translation for an unchanged segment, when the job is created, then that segment is carried over as `approved`.
- Given a job, when it is created, then the `localisation_editor` assigned to each locale is notified.

#### US-C-043 Translate and review with translation memory
As a **localisation editor**, I want **a side-by-side editor with translation memory and a glossary**, so that **terms stay consistent**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-C-042 · **Use case:** UC-C-11 · **Trace:** I18N
- Given a segment, when I edit it, then glossary terms and memory matches above 75% show beside it.
- Given a locale I am not assigned, when I try to edit it, then the API returns 403.
- Given I translated a segment, when it is reviewed, then a different `localisation_editor` for that locale must approve it.

#### US-C-044 Block graded items until the translation is approved
As a **content publisher**, I want **graded items used in a locale only after review**, so that **nobody is assessed on a bad translation**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-C-043 · **Use case:** UC-C-11 · **Trace:** I18N, ASM
- Given an item whose `fr` translation is not `approved`, when a learner sits it in `fr`, then the `en` text is served (US-L-039).
- Given a translation is approved, when the release is next published, then the locale becomes available.
- Given an approved translation is edited, when it saves, then its status returns to not approved.

#### US-C-045 Track localisation coverage
As a **content publisher**, I want **coverage per release and locale**, so that **I know what is ready**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-C-042 · **Use case:** UC-C-11 · **Trace:** I18N
- Given a release, when I open coverage, then the share of approved segments shows per locale and content type.
- Given coverage below 100% for graded items, when the view renders, then those items are listed first.
- Given a catalogue listing, when coverage for a locale is 100%, then the course shows that language as available.

### EP-C12 Resource library and learning asset management

#### US-C-046 Browse and search the resource library
As a **content author**, I want **to find library resources by type, concept, licence, and locale**, so that **I reuse what exists**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-111 · **Use case:** UC-C-01, UC-C-12 · **Trace:** CST, SRCH
- Given filters for kind, concept, taxonomy term, licence, locale, and state, when I apply them, then results update within 1 second.
- Given a resource, when I open it, then I see versions, rights, and where it is used.
- Given an `org` workspace author, when they search, then results include their workspace and `master` published resources only.

#### US-C-047 Reuse an asset across lessons
As a **content author**, I want **assets referenced rather than copied**, so that **one correction fixes every use**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-C-046 · **Use case:** UC-C-01, UC-C-12 · **Trace:** CST, KM
- Given an asset, when I attach it to a lesson, then the lesson references the asset by ID and pinned version.
- Given a new asset version, when it is published, then lessons using it are listed for update.
- Given an asset in use, when I try to archive it, then I am shown its uses and must confirm.

#### US-C-048 Detect duplicates and broken links
As a **knowledge steward**, I want **duplicate files and dead links found automatically**, so that **the library stays clean**.\
**Priority:** Should · **Size:** S · **Release:** R2 · **Dependencies:** US-110 · **Use case:** UC-C-01, UC-C-12 · **Trace:** KM
- Given an upload whose content hash matches an existing asset, when it completes, then I am shown the match and can link to it instead (US-110).
- Given the weekly link check, when an external link fails 3 times in a row, then it is flagged and its owner is notified.
- Given a flagged link, when it is fixed, then the flag clears on the next check.

#### US-C-049 Offer library resources to instructors
As a **content publisher**, I want **selected published resources available for instructors' overlays**, so that **instructors supplement courses with governed material**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-I-012 · **Use case:** UC-C-01, UC-C-12 · **Trace:** CST, INS
- Given a published resource marked "Available to instructors", when an instructor builds an overlay, then it can be added.
- Given a resource not marked, when an instructor searches for it, then it is not returned.
- Given a resource is archived, when cohorts use it in overlays, then their instructors are notified.

---

## 8. Platform

Platform stories have no screen of their own, or appear in every app. Their actor is often the platform itself on behalf of every user.

### EP-P01 Authorization and role assignments

#### US-P-001 Decide every request with scoped permissions
As a **platform architect**, I want **one policy engine to decide every protected action**, so that **access is consistent across five apps**.\
**Priority:** Must · **Size:** XL · **Release:** R1 · **Dependencies:** US-007 · **Use case:** UC-A-02, UC-O-03 · **Trace:** AUTHZ, TEN
- Given a request, when it is decided, then it is allowed only if a role assignment includes the permission, its scope contains the resource, and every attribute condition passes; otherwise it is denied.
- Given an explicit deny policy, when it matches, then it wins over any allow.
- Given a role change, when it is saved, then decisions reflect it within 60 seconds.
- Given every decision, when it is made for a protected write, then it is recorded in `authz.decision_log`.

#### US-P-002 Declare a permission for every endpoint
As a **platform architect**, I want **the build to fail when an endpoint has no declared permission**, so that **no route is accidentally open**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-P-001 · **Use case:** UC-A-02, UC-O-03 · **Trace:** AUTHZ, NFR
- Given a route without a permission declaration or an explicit public marker, when CI runs, then the build fails naming the route.
- Given a declared permission not in the permission catalogue, when CI runs, then the build fails.
- Given each route, when the test suite runs, then it has an allowed, a denied, and a cross-tenant test.

#### US-P-003 Migrate v1 roles to role assignments
As a **platform architect**, I want **v1 roles converted to v2 assignments**, so that **nobody gains or loses access in the move**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-P-001 · **Use case:** UC-A-02, UC-O-03 · **Trace:** AUTHZ, TEN
- Given v1 `student`, `instructor`, and `admin` users, when the migration runs, then they receive the assignments in the README mapping table.
- Given the migration runs twice, when it completes, then no duplicate assignments exist.
- Given every v1 route test, when it runs after the migration, then the same callers are allowed and denied as before.

#### US-P-004 Enforce app audience and MFA freshness
As a **security auditor**, I want **sensitive endpoints restricted by app audience and recent MFA**, so that **a stolen learner session cannot reach staff tools**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-P-001 · **Use case:** UC-A-02, UC-O-03 · **Trace:** AUTHZ, IAM
- Given a `/api/v1/platform` call, when its token `azp` is not the Admin App, then it returns 403.
- Given an action marked sensitive, when MFA was verified more than 10 minutes ago, then the API returns 401 with a step-up challenge.
- Given a Learner App token, when it calls an `/api/v1/content` write endpoint, then it returns 403.

#### US-P-005 Show the app launcher
As a **person with several roles**, I want **an app launcher listing only the apps I can open**, so that **I move between apps with one sign-in**.\
**Priority:** Must · **Size:** S · **Release:** R3 · **Dependencies:** US-P-001 · **Use case:** UC-A-02, UC-O-03 · **Trace:** PLT, AUTHZ
- Given `learner` and `instructor` assignments, when `GET /api/v1/me/apps` returns, then it lists the Learner App and the Instructor App only.
- Given an assignment is revoked, when 60 seconds pass, then the app leaves the launcher and its API calls return 403.
- Given I open an app from the launcher, when it loads, then I am not asked to sign in again.

### EP-P02 Events and integrations

#### US-P-006 Publish domain events through the outbox
As a **platform architect**, I want **events written in the same transaction as the change**, so that **no change is lost or announced without happening**.\
**Priority:** Must · **Size:** L · **Release:** R1 · **Dependencies:** None · **Use case:** UC-P-02 · **Trace:** EVT
- Given a state change that emits an event, when the transaction commits, then a CloudEvents 1.0 row with `tenantid`, `actorid`, and `correlationid` is in `events.outbox`; when it rolls back, then no row exists.
- Given the relay, when it runs, then events reach the `domain-events` topic with a 95th percentile lag under 5 seconds.
- Given an event, when it is inspected, then it holds identifiers and no free-text personal data.

#### US-P-007 Consume events idempotently
As a **platform architect**, I want **every consumer to ignore duplicate deliveries**, so that **at-least-once delivery is safe**.\
**Priority:** Must · **Size:** M · **Release:** R1 · **Dependencies:** US-P-006 · **Use case:** UC-P-02 · **Trace:** EVT
- Given the same event `id` delivered twice, when a consumer processes it, then `events.inbox` prevents a second effect.
- Given a consumer fails 5 times on an event, when retries are exhausted, then it goes to a dead-letter queue and an alert fires.
- Given a replay from the dead-letter queue, when it succeeds, then the effect happens once.

#### US-P-008 Register outbound webhooks
As an **organisation admin**, I want **signed webhooks for our organisation's events**, so that **our systems react to learning activity**.\
**Priority:** Should · **Size:** M · **Release:** R4 · **Dependencies:** US-P-006 · **Use case:** UC-P-02 · **Trace:** INT, EVT
- Given an HTTPS endpoint and chosen event types, when I register it, then deliveries are signed with HMAC-SHA256 and a timestamp.
- Given a failing endpoint, when deliveries fail, then they retry with exponential backoff for 24 hours and then stop, and I can see each attempt.
- Given an event from another organisation, when deliveries run, then it is never sent to my endpoint.

#### US-P-009 Export learning activity as xAPI and cmi5
As an **organisation admin**, I want **learning activity sent to our learning record store**, so that **it joins our other training data**.\
**Priority:** Could · **Size:** L · **Release:** R4 · **Dependencies:** US-P-006 · **Use case:** UC-P-02 · **Trace:** INT
- Given a configured learning record store, when lessons, assessments, and completions happen, then xAPI statements are sent within 15 minutes.
- Given a personal-account member, when statements are built, then only activity within their consent is included.
- Given the store rejects a statement, when it fails, then it is retried and logged in `integration.xapi_exports`.

### EP-P03 Notifications

#### US-P-010 Send notifications from events through localised templates
As a **platform architect**, I want **notifications produced from events and templates per locale**, so that **every module notifies the same way**.\
**Priority:** Must · **Size:** L · **Release:** R2 · **Dependencies:** US-P-007 · **Use case:** none · **Trace:** NTF, I18N
- Given `assessment.grade.released`, when the notification module consumes it, then an in-app and email notification are produced from the template in the recipient's locale.
- Given a template missing for `es`, when it renders, then the `en` template is used and the gap is logged.
- Given each delivery, when it is sent, then it is recorded in `notification.deliveries` with channel and status.

#### US-P-011 Manage my notification preferences
As a **user of any app**, I want **to choose categories, channels, and quiet hours**, so that **I get what I need without noise**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-P-010 · **Use case:** none · **Trace:** NTF
- Given preferences, when I turn off email for "Social", then no social emails are sent and in-app items still appear.
- Given quiet hours from 22:00 to 07:00, when a non-urgent notification is due, then it is held until 07:00 in my timezone.
- Given a mandatory category such as security or assessment deadlines, when I try to turn it off, then the control is locked.

#### US-P-012 Receive digests
As a **user of any app**, I want **grouped digests instead of single messages**, so that **my inbox stays manageable**.\
**Priority:** Should · **Size:** M · **Release:** R2 · **Dependencies:** US-P-011 · **Use case:** none · **Trace:** NTF
- Given daily digest for a category, when 08:00 in my timezone arrives, then pending items are sent as one message.
- Given no pending items, when the digest runs, then nothing is sent.
- Given an urgent item, when it occurs, then it is sent immediately regardless of digest settings.

#### US-P-013 Apply organisation branding and policy to notifications
As an **organisation admin**, I want **notifications to our members to carry our branding and follow our rules**, so that **messages look official and compliant**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-O-014, US-P-010 · **Use case:** none · **Trace:** NTF, TEN
- Given a notification in my organisation's context, when it renders, then it uses my organisation's templates and sender name.
- Given my organisation disables SMS, when a member has SMS on, then SMS is not sent for my organisation's notifications.
- Given a personal-account member, when they receive a consumer notification, then it does not carry my branding.

### EP-P04 Search

#### US-P-014 Index content changes from events
As a **platform architect**, I want **the search index updated from events**, so that **results reflect current content**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-P-007 · **Use case:** UC-L-09 · **Trace:** SRCH, EVT
- Given `content.release.published` or `knowledge.asset_version.published`, when it is consumed, then the index updates within 60 seconds.
- Given `content.release.archived`, when it is consumed, then the content leaves learner results within 60 seconds.
- Given a full reindex, when it runs, then search continues on the old index until the new one is complete.

#### US-P-015 Filter search by tenant and permission
As a **security auditor**, I want **search results filtered by tenant and permission at query time**, so that **search never leaks data**.\
**Priority:** Must · **Size:** M · **Release:** R2 · **Dependencies:** US-P-014, US-P-001 · **Use case:** UC-L-09 · **Trace:** SRCH, TEN, AUTHZ
- Given every indexed document, when it is stored, then it carries `tenant_id`, workspace, visibility, and state.
- Given a query, when it runs, then filters for the active tenant, entitlements, and permission are applied before ranking.
- Given an automated test across two organisations and three apps, when it runs, then no result outside the caller's scope is returned.

#### US-P-016 Search people within scope
As an **instructor or organisation admin**, I want **to find people I am responsible for**, so that **I can act on them quickly**.\
**Priority:** Should · **Size:** S · **Release:** R3 · **Dependencies:** US-P-015 · **Use case:** UC-L-09 · **Trace:** SRCH, INS, ORG
- Given an instructor, when they search people, then only learners and staff in their cohorts are returned.
- Given an `org_admin`, when they search, then members of their organisation are returned.
- Given a learner, when they call people search, then the API returns 403.

#### US-P-017 Remove erased data from every index
As an **organisation compliance officer**, I want **erased accounts removed from search and retrieval**, so that **erasure is complete**.\
**Priority:** Must · **Size:** S · **Release:** R2 · **Dependencies:** US-P-007, US-009 · **Use case:** UC-L-09 · **Trace:** SRCH, NFR
- Given `identity.account.erased`, when search and retrieval consume it, then the person's documents and vectors are removed within 24 hours.
- Given removal completes, when the consumer finishes, then a completion record is written for the data subject request.
- Given a search for the erased person's name, when it runs after removal, then nothing is returned.

---

## 9. Traceability

| Epic | Use case | Stories | Releases | Must | Should | Could |
| --- | --- | --- | --- | :-: | :-: | :-: |
| EP-L01 Organisations and tenant context | UC-L-01, UC-L-02 | US-L-001 to US-L-004 | R1, R3 | 3 | 1 | 0 |
| EP-L02 Cohort plans and assignments | UC-L-03, UC-L-04 | US-L-005 to US-L-008 | R3 | 4 | 0 | 0 |
| EP-L03 Grades and feedback | UC-L-05 | US-L-009 to US-L-012 | R3 | 1 | 3 | 0 |
| EP-L04 Mentor modes and persona | UC-L-06 | US-L-013 to US-L-016 | R2 | 2 | 2 | 0 |
| EP-L05 Personalisation dimensions | UC-L-07 | US-L-017 to US-L-020 | R2, R3 | 2 | 2 | 0 |
| EP-L06 Scoped leaderboards, competitions, and challenges | UC-L-08, UC-P-03 | US-L-021 to US-L-025 | R2, R3 | 2 | 1 | 2 |
| EP-L07 Knowledge search | UC-L-09 | US-L-026 to US-L-029 | R2, R3 | 2 | 2 | 0 |
| EP-L08 Career planning and learning passport | UC-L-10, UC-L-11 | US-L-030 to US-L-033 | R2, R4 | 0 | 3 | 1 |
| EP-L09 Learner analytics | v1 UC-20 | US-L-034 to US-L-037 | R2, R3 | 1 | 2 | 1 |
| EP-L10 Localisation of all surfaces | v1 UC-22 | US-L-038 to US-L-041 | R2, R3 | 2 | 1 | 1 |
| EP-I01 Learner management: create, bulk import, invite | UC-I-01, UC-I-02 | US-I-001 to US-I-005 | R3 | 4 | 1 | 0 |
| EP-I02 Cohort management | UC-I-03 | US-I-006 to US-I-009 | R3 | 3 | 1 | 0 |
| EP-I03 Curriculum assignment and scheduling with overlays | UC-I-04, UC-I-14 | US-I-010 to US-I-013 | R3 | 3 | 1 | 0 |
| EP-I04 Assessment creation and quiz builder | UC-I-05 | US-I-014 to US-I-017 | R3 | 3 | 1 | 0 |
| EP-I05 Rubrics and manual marking | UC-I-06, UC-I-07 | US-I-018 to US-I-021 | R3 | 3 | 1 | 0 |
| EP-I06 AI-assisted marking and override | UC-I-08, UC-I-09 | US-I-022 to US-I-026 | R3 | 3 | 2 | 0 |
| EP-I07 Progress, risk monitoring, and interventions | UC-I-10 | US-I-027 to US-I-030 | R3 | 2 | 1 | 1 |
| EP-I08 Attendance and engagement | UC-I-11 | US-I-031 to US-I-034 | R3 | 0 | 3 | 1 |
| EP-I09 Communication hub | UC-I-12 | US-I-035 to US-I-038 | R3 | 2 | 2 | 0 |
| EP-I10 Performance analytics | UC-I-13 | US-I-039 to US-I-042 | R3 | 1 | 2 | 1 |
| EP-O01 Organisation setup and structure | UC-O-01, UC-O-02 | US-O-001 to US-O-004 | R3 | 4 | 0 | 0 |
| EP-O02 Instructor and cohort administration | UC-O-03, UC-O-04 | US-O-005 to US-O-008 | R3 | 3 | 1 | 0 |
| EP-O03 Licences, seats, and billing | UC-O-05 | US-O-009 to US-O-012 | R3 | 3 | 1 | 0 |
| EP-O04 Branding and domains | UC-O-06 | US-O-013 to US-O-016 | R3, R4 | 0 | 3 | 1 |
| EP-O05 SSO, SCIM, and LTI | UC-O-07, UC-O-08, UC-O-13, UC-P-01 | US-O-017 to US-O-020 | R3, R4 | 3 | 1 | 0 |
| EP-O06 Reporting and learning analytics | UC-O-09, UC-P-04 | US-O-021 to US-O-024 | R3 | 2 | 2 | 0 |
| EP-O07 Workforce development reporting | UC-O-10 | US-O-025 to US-O-028 | R4 | 2 | 1 | 1 |
| EP-O08 Compliance and policies | UC-O-11, UC-O-12 | US-O-029 to US-O-032 | R3 | 3 | 1 | 0 |
| EP-A01 Platform user administration | UC-A-02 | US-A-001 to US-A-004 | R2 | 3 | 1 | 0 |
| EP-A02 Organisation provisioning | UC-A-01 | US-A-005 to US-A-008 | R3 | 2 | 2 | 0 |
| EP-A03 AI services and model management | UC-A-03 | US-A-009 to US-A-012 | R2, R3 | 3 | 1 | 0 |
| EP-A04 Feature flags and settings | UC-A-04 | US-A-013 to US-A-016 | R2 | 2 | 1 | 1 |
| EP-A05 Audit and security monitoring | UC-A-05, UC-A-06, UC-A-10 | US-A-017 to US-A-020 | R2, R3 | 3 | 1 | 0 |
| EP-A06 Subscriptions and global reporting | UC-A-07, UC-A-08 | US-A-021 to US-A-024 | R2, R4 | 2 | 1 | 1 |
| EP-A07 Content and knowledge governance oversight | UC-A-09 | US-A-025 to US-A-028 | R2 | 2 | 1 | 1 |
| EP-C01 Knowledge repository and asset management | UC-C-01 | US-C-001 to US-C-004 | R1, R2 | 4 | 0 | 0 |
| EP-C02 Lesson builder | UC-C-02 | US-C-005 to US-C-008 | R2 | 2 | 2 | 0 |
| EP-C03 Course, module, and curriculum builder | UC-C-03 | US-C-009 to US-C-012 | R2, R3 | 3 | 1 | 0 |
| EP-C04 Learning path builder | UC-C-04 | US-C-013 to US-C-016 | R2 | 2 | 2 | 0 |
| EP-C05 Quiz builder and item bank | UC-C-05 | US-C-017 to US-C-020 | R2, R3 | 3 | 0 | 1 |
| EP-C06 Taxonomy and metadata | UC-C-06 | US-C-021 to US-C-024 | R2 | 1 | 2 | 1 |
| EP-C07 Knowledge graph management | UC-C-07 | US-C-025 to US-C-028 | R2 | 2 | 2 | 0 |
| EP-C08 Versioning and releases | UC-C-09 | US-C-029 to US-C-032 | R2 | 2 | 2 | 0 |
| EP-C09 Review and publishing workflow | UC-C-08, UC-C-09, UC-C-12 | US-C-033 to US-C-037 | R1, R2 | 5 | 0 | 0 |
| EP-C10 AI content generation | UC-C-10 | US-C-038 to US-C-041 | R2 | 2 | 2 | 0 |
| EP-C11 Localisation workflow | UC-C-11 | US-C-042 to US-C-045 | R2 | 3 | 1 | 0 |
| EP-C12 Resource library and learning asset management | UC-C-01, UC-C-12 | US-C-046 to US-C-049 | R2, R3 | 1 | 3 | 0 |
| EP-P01 Authorization and role assignments | UC-A-02, UC-O-03 | US-P-001 to US-P-005 | R1, R2, R3 | 5 | 0 | 0 |
| EP-P02 Events and integrations | UC-P-02 | US-P-006 to US-P-009 | R1, R4 | 2 | 1 | 1 |
| EP-P03 Notifications | none | US-P-010 to US-P-013 | R2, R3 | 2 | 2 | 0 |
| EP-P04 Search | UC-L-09 | US-P-014 to US-P-017 | R2, R3 | 3 | 1 | 0 |
| **Total (51 epics)** | **51** | **209** | | **122** | **71** | **16** |

Totals by application: Learner App 41 stories, Instructor App 42, Institution App 32, Admin App 28, Content Studio 49, Platform 17.

## 10. Stories by actor

Actors are role IDs from the README. A story is listed under the role in its "As a" line; roles that only appear in a story's permission checks are listed as "Constrained in".

| Actor | Stories |
| --- | --- |
| Guest (no account) | Interacts in US-L-021 (pseudonymous global board) |
| `learner` (personal, managed, and cohort learners) | US-L-001 to US-L-041 |
| `teaching_assistant` | US-I-019. Constrained in US-I-004, US-I-007, US-I-011, US-I-021, US-I-023, US-I-034 |
| `instructor` | US-I-001 to US-I-005, US-I-010 to US-I-019, US-I-021 to US-I-023, US-I-027 to US-I-033, US-I-035 to US-I-037, US-I-039, US-I-040, US-I-042, US-C-031, US-P-016 |
| `lead_instructor` | US-I-006 to US-I-009, US-I-020, US-I-024, US-I-025, US-I-034, US-I-041 |
| `department_admin`, `campus_admin` | US-O-005 to US-O-007, US-O-026 |
| `org_admin` | US-O-002 to US-O-004, US-O-008, US-O-013, US-O-014, US-O-016 to US-O-020, US-O-024, US-O-025, US-O-027, US-P-008, US-P-009, US-P-013, US-P-016 |
| `org_owner` | US-O-001, US-O-015, US-O-028. Constrained in US-O-004 |
| `org_billing_manager` | US-O-009 to US-O-012 |
| `org_report_viewer` | US-O-021, US-O-022. Constrained in US-O-024 |
| `org_compliance_officer` | US-I-026, US-I-038, US-O-023, US-O-029 to US-O-032, US-P-017 |
| `content_author` (in `master` or an `org` workspace) | US-C-001, US-C-002, US-C-004 to US-C-010, US-C-012 to US-C-015, US-C-017, US-C-018, US-C-023, US-C-029, US-C-033, US-C-038, US-C-046, US-C-047 |
| `content_reviewer` | US-C-011, US-C-031, US-C-034, US-C-040 |
| `content_publisher` | US-C-003, US-C-016, US-C-020, US-C-030, US-C-032, US-C-035 to US-C-037, US-C-042, US-C-044, US-C-045, US-C-049 |
| `knowledge_steward` | US-C-019, US-C-021, US-C-022, US-C-024 to US-C-028, US-C-041, US-C-048 |
| `localisation_editor` | US-C-039, US-C-043 |
| `support_agent` | US-A-004 |
| `finance_admin` | US-A-006, US-A-021, US-A-022 |
| `ai_admin` | US-A-009 to US-A-012 |
| `platform_operator` | US-A-013 to US-A-016 |
| `security_auditor` | US-A-017 to US-A-019, US-P-004, US-P-015 |
| `platform_admin` | US-A-001 to US-A-003, US-A-005, US-A-007, US-A-008, US-A-020, US-A-023 to US-A-028 |
| Any signed-in person | US-P-005, US-P-011, US-P-012 |
| Platform architect (engineering owner, not a role) | US-P-001 to US-P-003, US-P-006, US-P-007, US-P-010, US-P-014 |
| `system` principals | Interact in US-L-001, US-C-003, US-I-028, US-O-019, US-P-006, US-P-007, US-P-010, US-P-014, US-P-017 |

## 11. Suggested delivery order

The order follows the dependency chains in each story and the release themes in the README. Each phase ends with something a person can use. Must stories are planned first; Should and Could stories fill remaining capacity in their release.

| Release | Phase | Stories |
| --- | --- | --- |
| R1 | Foundations that are expensive to retrofit: scoped authorization, v1 role migration, outbox, consumer organisation | US-P-001 to US-P-003, US-P-006, US-P-007, US-L-001 |
| R1 | Content Studio split from the admin portal with the v1 workflow on the new state names | US-C-003, US-C-004, US-C-033 to US-C-036, plus the v1 Epic 15 Must stories |
| R1 | Learner App closed beta | v1 Epics 1 to 14 Must stories, per [UseCases.md section 10](../UseCases.md#10-suggested-delivery-order) |
| R2 | Admin App v1 | US-A-001 to US-A-003, US-A-009 to US-A-011, US-A-013, US-A-014, US-A-017, US-A-018, US-A-021, US-A-023, US-A-025, US-A-027, US-P-004 |
| R2 | Content Studio v1: builders, graph, releases, localisation | US-C-001, US-C-002, US-C-005, US-C-007, US-C-009 to US-C-011, US-C-013, US-C-016 to US-C-018, US-C-021, US-C-025, US-C-026, US-C-029, US-C-030, US-C-037, US-C-040 to US-C-044, US-C-046 |
| R2 | Public launch learner features and shared services | US-L-013, US-L-016, US-L-017, US-L-021, US-L-022, US-L-026, US-L-038, US-P-010, US-P-011, US-P-014, US-P-015, US-P-017 |
| R2 | Should and Could stories, ranked by value | US-L-015, US-L-019, US-L-024, US-L-027, US-L-034, US-C-006, US-C-031, US-C-038, US-A-004, US-A-015, US-P-012, then the rest |
| R3 | Tenancy and structure | US-A-005, US-A-006, US-A-020, US-O-001 to US-O-004, US-O-009 to US-O-011, US-O-017, US-L-002, US-L-003, US-L-037, US-P-005 |
| R3 | Cohorts and plans | US-I-001 to US-I-004, US-I-006 to US-I-008, US-I-010 to US-I-012, US-O-005, US-O-006, US-O-008, US-L-005, US-L-006, US-L-018, US-L-028 |
| R3 | Assessment and marking | US-I-014, US-I-016 to US-I-019, US-I-021 to US-I-023, US-I-026, US-I-042, US-C-020, US-L-007 to US-L-009, US-L-039 |
| R3 | Monitoring, communication, reporting, compliance | US-I-027, US-I-028, US-I-035, US-I-036, US-O-021, US-O-023, US-O-029, US-O-030, US-O-032 |
| R3 | Should and Could stories, ranked by value | US-I-024, US-I-025, US-I-013, US-L-010, US-L-011, US-I-029, US-I-031, US-I-032, US-O-022, US-A-008, US-C-012, then the rest |
| R4 | Enterprise integration and workforce reporting | US-O-019, US-O-020, US-O-025, US-O-026, then US-O-015, US-O-018, US-O-027, US-L-032, US-P-008 |
| R4 | Could stories | US-L-033, US-O-028, US-A-024, US-P-009 |
| R5 | Ecosystem | No stories yet. See [Open questions](#13-open-questions) |

## 12. Definition of ready and done additions

These add to the team's existing definitions; they do not replace them. They apply to every story that touches tenant-scoped data or a protected action.

| Check | Ready (before the sprint) | Done (before the story closes) |
| --- | --- | --- |
| Tenant isolation | The story names the tenant-scoped resources it reads or writes and the scope at which they live | Automated tests prove that a user in another organisation gets 404 for every resource the story exposes, and that PostgreSQL row-level security on `app.tenant_id` is active for every new table |
| Permission declared | Each protected action names its permission in `<context>.<resource>:<action>` form, and new permissions are added to [10-rbac-matrix.md](10-rbac-matrix.md) | The route declares the permission (US-P-002); tests cover one allowed, one denied (403), and one cross-tenant (404) case |
| Events documented | Events the story emits or consumes are named in the README format and listed in [08-api-specification.md](08-api-specification.md) | Events are written through `events.outbox` in the same transaction, carry `tenantid`, `actorid`, and `correlationid`, and contain no free-text personal data; consumers are idempotent on event `id` |
| Localisation | New user-facing strings are identified | Message keys exist in `en`, `fr`, and `es` catalogues (machine translation is acceptable for UI strings until reviewed); dates and numbers use locale formatting; graded content follows `translation_status` |
| Accessibility | The design meets the [DesignSpec](../DesignSpec.md) design system | The screen meets WCAG 2.2 AA: keyboard operable, visible focus, 4.5:1 text contrast, labelled controls, and an automated axe check with no serious or critical issues |
| Audit | Privileged or staff actions are identified | Each such action writes an audit entry with tenant, actor, target, before, after, and reason where required |
| Release and flag | The story has a release and, if partial in that release, a feature flag key in `<app_or_context>.<feature>` form | The flag has an owner and a removal date |

## 13. Open questions

These need a decision from product, learning, or engineering before the related stories are estimated.

1. **Use case numbers.** This document assumes one use case per epic (`UC-I-04, UC-I-14` for `EP-I03`). [04-use-cases.md](04-use-cases.md) may number differently; it wins.
2. **Friends.** US-L-023 needs a friend connection entity that the README schema list does not include (`game` gains `competitions`, `seasons`, `leaderboard_scopes` only). The cap of 200 friends and the managed-account rule are proposals.
3. **Leaderboard periods and seasons.** US-L-021 and US-L-024 use the periods in README (weekly, monthly, season as a calendar quarter, all time). Open: whether weekly resets follow Monday 00:00 UTC (v1 BR-23) or the learner's local week.
4. **Who runs platform challenges and competitions.** The README names no role for gamification configuration. This document proposes `platform_operator` in the Admin App for schedules and `content_author` in Content Studio for challenge items (amending US-072 and US-073), and `lead_instructor` for cohort competitions.
5. **Regrades and second marking.** US-L-011 and US-I-020 need regrade request and moderation records that the README `assessment` schema list does not include.
6. **Delegation to teaching assistants.** The README lets a `teaching_assistant` release grades when delegated. US-I-023 also assumes override can be delegated. Confirm.
7. **Policy defaults.** Shared defaults (regrade window, AI-marking pause, invitation expiry, import limit, break-glass window, risk thresholds) are fixed in README §Shared defaults. Still open: the second-marking disagreement threshold of 10 percentage points (US-I-021) and the inactive-seat flag at 90 days.
8. **Privacy thresholds.** v1 hides segments under 10 learners. This document uses 10 for learner comparisons, 5 for item statistics and workforce heatmap cells, and 5 organisations and 10 learners for benchmarks. One platform rule is needed.
9. **Platform admin rights in Content Studio.** The README gives `platform_admin` read access to Content Studio, but the v1 emergency override of the two-person rule (US-123, carried into US-C-035) is a write. Decide whether the override stays with `platform_admin` or moves to `content_publisher` with a second approver.
10. **AI budgets.** US-A-012 proposes "degrade" and "block" behaviours at 100% of an organisation's monthly AI budget. Commercial terms must define which applies per plan.
11. **Upload limits.** US-C-001 keeps 50 MB for documents (v1) and proposes 2 GB for video. Storage cost and transcoding are not yet designed.
12. **Workforce skill frameworks.** US-O-025 assumes job roles and imported skill frameworks are organisation-owned data mapped to concepts. Their schema and owning module (`reporting` or `knowledge`) are undecided.
13. **R5 scope.** The content marketplace, AI agent orchestration, the Instructor mobile app, and the partner API have no stories. They need epics (for example `EP-C13` and `EP-P05`) once ADR 0027 is accepted.
