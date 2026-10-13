# ADR 0019 — Content Studio, content ownership, and versioned content releases

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13
- Amends: [ADR 0009](0009-knowledge-repository.md) (the catalog module stops being the runtime source of truth)

## Context

ADR 0009 makes `backend/app/domain/catalog.py` the source the process trusts at runtime; startup seed upserts Postgres rows from it. Edits are pull requests. ADR 0011 adds a database workflow for knowledge asset versions (`draft → review → approved → published → archived`, enforced by trigger and recorded in `knowledge.workflow_transitions`), but courses, modules, and paths have no versions, and a learner who started on revision A cannot finish it (ADR 0009 future consideration).

The v2 direction gives content to a governed team (platform admins, SMEs, curriculum designers), lets institutions assign courses to cohorts on a schedule, and lets instructors customise without changing the master. Institutions also need private content.

## Problem

Decide who owns content, how it moves from draft to learners, how published content is versioned so cohorts are not disrupted mid-term, and how institutions and instructors customise it.

## Decision

**Content Studio** is a first-class app ([ADR 0013](0013-five-applications-shared-platform.md)) for content authors, reviewers, publishers, knowledge stewards, and localisation editors. Its API root is `/api/v1/content/...`.

**Workspaces** (`curriculum.workspaces`) are ownership boundaries. Every authored row carries `workspace_id`.

| Workspace kind | Owner | Who can author | Visible to |
| --- | --- | --- | --- |
| `master` | The platform content organisation | Holders of Content Studio roles in `master` | All tenants, through the catalogue and licences |
| `org` | One organisation (licence feature) | Holders of Content Studio roles in that workspace | That organisation only |

**Workflow.** Every content type (asset, lesson, module, course, path, assessment item) uses `draft → in_review → approved → published → archived`. A reviewer may send `changes_requested`, which returns the item to `draft` with comments. The v1 enum value `review` is renamed `in_review`.

**Two-person rule.** The person who approves cannot be an author of the version. In `master` the rule is mandatory. In an `org` workspace it is on by default and an `org_admin` may turn it off. The database trigger that already guards asset transitions is extended to all content tables.

**Content releases.** Publishing a course or learning path creates an immutable release (`curriculum.course_releases`, `curriculum.path_releases`) that snapshots the exact version of every lesson, module, check, and asset in `curriculum.release_items`. Releases use `MAJOR.MINOR.PATCH`:

| Bump | When |
| --- | --- |
| MAJOR | A lesson or graded assessment removed, concepts or outcomes changed, or order changed so progress cannot carry over |
| MINOR | Lessons, checks, or locales added; nothing removed |
| PATCH | Corrections to text, media, or translations with no structural change |

**Pinning.** A cohort plan pins one release. PATCH releases advance pinned cohorts automatically unless an assessment in the plan is open. MINOR and MAJOR releases are offered to the instructor, who accepts or declines. Self-directed enrolments follow the latest release at the next module boundary. Progress is keyed by concept and lesson id, so it carries across releases.

**Customisation.**

| Mechanism | Who | What it can do | Master changed |
| --- | --- | --- | --- |
| Overlay | Instructor (cohort), org admin (organisation) | Reorder, hide, add supplementary items, set dates, add instructions | Never |
| Derived course | Organisation with an `org` workspace | Copy a master release into the workspace and edit freely; `derived_course_links` records the upstream release, and new upstream releases appear as a reviewable diff | Never |

**Seed migration.** `catalog.py` becomes a one-time seed import into the `master` workspace as release `1.0.0` of each course and path (R1). After R2 the catalog is no longer read at runtime, and startup seed stops upserting lesson bodies.

**Rights metadata.** Every knowledge asset records `rights` (owner, source, `licence_terms` such as `CC-BY-4.0`, `proprietary`, `publisher-licensed`), attribution text, and allowed uses (display, RAG grounding, AI generation input). Publishing is blocked when rights are missing; retrieval honours allowed uses.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Keep the catalog file as the source with a draft overlay | Non-developers cannot edit Python. Institutions cannot own private content in a repository file. |
| Headless CMS (Contentful, Sanity, Strapi) | Concept ids, prerequisites, answer keys, and mastery hooks would live outside the database the API and RLS use, and the workflow would bypass the audit trail. |
| Live content with no releases | An edit during term changes what a cohort is assessed on. |
| Instructors edit master copies | Breaks governance and makes quality accountability impossible. |
| Git-backed content repository | Strong history, but approval, rights, and per-locale workflows would be rebuilt on top of pull requests for non-technical authors. |

## Trade-off analysis

Immutable releases cost storage (release items reference versions, not copies, so the cost is rows, not bodies) and add a publish step. They let a cohort finish on the release it started and let a reviewer see exactly what changed.

Overlays cover most instructor needs without forking. Derived courses are the escape hatch and carry merge cost; they are a licence feature so that cost is chosen deliberately.

## Consequences

- `ref.content_status` gains `in_review`; `review` is migrated. Workflow transitions are recorded for every content type.
- Events `content.release.published`, `content.release.archived`, and `content.item.state_changed` drive retrieval re-indexing, search, and notifications ([ADR 0018](0018-event-outbox.md)).
- [14-content-studio-specification.md](../platform/14-content-studio-specification.md) defines the builders and screens.

## Future considerations

- Scheduled publishing and embargoed releases.
- Marketplace listings of `publisher` organisation releases ([ADR 0027](0027-extension-points.md)).
