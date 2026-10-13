# AI Mentor Content Studio specification

| Field | Value |
| --- | --- |
| Document | 14 — Content Studio specification |
| Version | 2.0 |
| Date | 13 October 2026 |
| Status | Approved direction. Target application; content screens today live in `admin/` until the R1 split |
| Owner | Learning (CLO) for pedagogy and workflow; Product Design for screens; Engineering for `/api/v1/content` |
| Related | [README.md](README.md), [02-prd.md](02-prd.md) C-F01–C-F14, [03-srs.md](03-srs.md), [04-use-cases.md](04-use-cases.md) UC-C-01–12, [11-ux-specification.md](11-ux-specification.md) §12, [12-information-architecture.md](12-information-architecture.md) §8, [13-knowledge-management-architecture.md](13-knowledge-management-architecture.md), [../Admin.md](../Admin.md), [../Knowledge-Catalog.md](../Knowledge-Catalog.md), [../DesignSpec.md](../DesignSpec.md) §15–16, ADR 0013, 0019, 0020, 0023 |

## Change record

| Area | What changed | Why | Impacted systems | Implementation implications |
| --- | --- | --- | --- | --- |
| Application | Content Studio is specified as its own Next.js app (`apps/studio`, `studio.<domain>`, port 3004), not a section of the Admin App | ADR 0013: content operations and platform operations have different users, density, and release cadence | `admin/`, new `apps/studio`, Clerk `azp`, CORS | R1 splits `admin/` content routes into Studio; API root `/api/v1/content` |
| Ownership | Master repository belongs to platform content roles; instructors never edit master | Quality and licensing at multi-tenant scale (ADR 0019) | `content`, `knowledge`, Instructor App overlays | Workspace-scoped roles; overlays and derived courses instead of forks |
| Hierarchy | Builders follow Knowledge Asset → Lesson → Module → Course → Learning Path | Matches the content model in the README | `content`, `knowledge` | Course is the assignable, releasable unit; paths compose courses |
| Workflow | Two-person review, immutable releases, localisation jobs, AI drafts with provenance | Cohorts pin releases; generated content must be attributable | `content`, `retrieval`, `i18n`, `ai_gateway` | Semver releases; answer keys never leave `/content` |
| Resource Catalog | Knowledge Pack v1.0 and catalog import screens move from `admin/` `/catalog` to Studio Library and Import | Previous implementation parked catalog in the Admin App because Studio did not exist yet | `apps/studio`, `/api/v1/content`, `knowledge` | Keep `/api/v1/admin/catalog/*` as aliases until R2; Learner App keeps `/learn` search |

## Relationship to v1 documents

| v1 source | Status | Notes |
| --- | --- | --- |
| [Admin.md](../Admin.md) | Retained as the original brief | Every capability is allocated here or to the Admin App |
| [DesignSpec.md](../DesignSpec.md) §15–16 | Superseded for content screens | Wireframe intent kept; routes and roles follow ADR 0013 |
| [Knowledge-Catalog.md](../Knowledge-Catalog.md) | Describes running catalog code | Target home is this app; learner search stays in the Learner App |
| [13](13-knowledge-management-architecture.md) | Complementary | 13 owns services, pipelines, and data; this document owns journeys, screens, and builder rules |
| [11](11-ux-specification.md) §12 | Complementary | Shared shell, tokens, and components; this document owns Studio-only screens |

## Contents

1. [Purpose and users](#1-purpose-and-users)
2. [One API, this app](#2-one-api-this-app)
3. [Roles and permissions](#3-roles-and-permissions)
4. [Navigation and dashboard](#4-navigation-and-dashboard)
5. [Knowledge repository and resource library](#5-knowledge-repository-and-resource-library)
6. [Builders](#6-builders)
7. [Taxonomy, graph, and metadata](#7-taxonomy-graph-and-metadata)
8. [Review and publishing](#8-review-and-publishing)
9. [Releases](#9-releases)
10. [AI generation](#10-ai-generation)
11. [Localisation](#11-localisation)
12. [Analytics](#12-analytics)
13. [R1 and R2 split](#13-r1-and-r2-split)
14. [Open questions](#14-open-questions)

---

## 1. Purpose and users

Content Studio is the first-class application for knowledge management, curriculum creation, content operations, and educational asset management. It is not a staff corner of the Admin App and it is not a teaching tool. Instructors consume released courses in the Instructor App; they do not own the master repository.

| Person | Typical roles in a workspace | Job in this app |
| --- | --- | --- |
| Subject-matter expert | `content_author`, sometimes `content_reviewer` | Write and review technical accuracy |
| Curriculum designer | `content_author` | Structure courses, paths, outcomes, assessment blueprints |
| Content editor / producer | `content_author`, sometimes `content_publisher` | Production, media, accessibility, release operations |
| Knowledge steward | `knowledge_steward` | Taxonomy, concept graph, metadata schemas, vocabularies |
| Localisation editor | `localisation_editor` | Translate and approve locale variants |
| Reviewer / publisher | `content_reviewer`, `content_publisher` | Two-person approval and immutable releases |
| Platform admin | `platform_admin` | Read everything; emergency take-down only (`content.item:take_down`) |

A person who also teaches uses the Instructor App for cohorts and marking. Cross-app links ("View as learner", "Open in Studio") are defined in [12](12-information-architecture.md#10-deep-links-across-apps).

## 2. One API, this app

The backend stays one FastAPI modular monolith (ADR 0002, 0017). Content Studio is a Next.js client of that API.

| Item | Value |
| --- | --- |
| Origin | `studio.<domain>` (local port 3004) |
| Source (target) | `apps/studio` |
| Source (today) | Content half of `admin/` — library, review, curriculum, taxonomy, graph, generate, challenges, catalog |
| Clerk audience | `studio` (`azp`) |
| API root | `/api/v1/content/...` |
| Tenant context | Workspace slug in the path (`/w/{workspaceSlug}/…`); `master` or an organisation slug |
| Branding | Studio accent token only. Never tenant branding (11 §12) |
| Phones | Read, comment, and review decisions. Builders are desktop-first |

The API enforces every permission. The app's route guard only decides what to render. A stolen Learner App session cannot call `/content` even if the person holds a Studio role (ADR 0013).

Modules this app talks to: `knowledge`, `content`, `retrieval`, `ai_gateway`, `i18n`, `search`, `analytics`, `audit`. It never writes `classroom`, `assessment` issued copies, or `gamification` ledgers.

## 3. Roles and permissions

Assignments are workspace-scoped. Permission names come from the README.

| Screen family | Minimum role | Representative permissions |
| --- | --- | --- |
| Library browse | any Studio role | `knowledge.asset:read` |
| Upload / edit draft | `content_author` | `knowledge.asset:upload`, `content.item:edit` |
| Taxonomy, graph, schemas | `knowledge_steward` | `knowledge.taxonomy:edit`, `knowledge.concept_relation:edit` |
| Review queue | `content_reviewer` | `content.item:review` (cannot approve own work) |
| Publish release | `content_publisher` | `content.course:publish`, `content.path:publish` |
| Localisation | `localisation_editor` | `content.translation:edit` |
| Take-down | `platform_admin` | `content.item:take_down` |

Answer keys, hidden tests, and rights attestations are returned only on `/content` to roles that hold `content.item:read_key`. Learner and Instructor clients never receive them.

## 4. Navigation and dashboard

Primary navigation is fixed (12 §8.2): Home, Library, Build, Knowledge, Review, Releases, Localisation.

**Home** (`/w/{slug}`) shows four queues the signed-in person can act on: my drafts, assigned reviews, scheduled releases, and content-health exceptions (broken links, stale translations, graph issues). Counts come from `GET /api/v1/content/workspaces/{id}/home`.

**Content health** (`/health`) is the steward and publisher queue: graph issues, missing rights, expired external links, stale locales, assets used by a pinned release that failed verification.

**Insights** (`/insights`) is C-F14: completion, struggle concepts, and asset usefulness, scoped to the workspace. It is not the Admin App's platform analytics.

## 5. Knowledge repository and resource library

This is C-F01 and C-F02. The running Resource Catalog ([Knowledge-Catalog.md](../Knowledge-Catalog.md)) is the seed of this library: Knowledge Pack v1.0 plus import jobs become `master` workspace assets.

### 5.1 Asset kinds

The 13 kinds from the README content model: PDF, book, research paper, lecture notes, presentation, video, dataset, repository, external link, image, audio, assessment, lesson content. File format is a separate attribute of the version.

### 5.2 Library screens

| Route | Job |
| --- | --- |
| `/library` | Faceted list: kind, taxonomy, concept, locale, rights, state, quality score |
| `/library/upload` | Add file or URL, choose kind, rights and licence terms, concepts |
| `/library/collections` | Curated lists (for example "RL primary papers") |
| `/library/{assetId}` | Metadata, preview, versions, usage ("where used"), replace, retire |
| `/library/{assetId}/versions` | Compare two versions; restore creates a new draft, never mutates a release |

Import centre (today `admin/catalog/import`): bulk JSON, registered sources (Microsoft Learn, Coursera, arXiv, GitHub, …), scheduled refresh, duplicate detection, quality scoring. Remote harvests skip without credentials. Duplicates merge by archiving the loser (running behaviour kept).

**Rights.** Submit-for-review is refused when `rights` is missing or `unknown` (UC-C-01 E1). Retrieval honours allowed uses (display, RAG, generation input).

**Ingestion.** Upload stores a draft version and starts the worker pipeline in 13. Chunks are retrievable only after `knowledge.asset_version.published`.

## 6. Builders

Hierarchy, smallest unit first. Every builder uses the shared `WorkflowStatusBadge`, validation summary, and "Preview as learner" (same renderer as the Learner App).

### 6.1 Lesson builder (C-F03, UC-C-02)

A lesson has a primary concept, objectives, estimated minutes, a body per locale and teaching approach, linked assets (roles in 13), and checks that measure the concepts. It cannot enter `in_review` without a primary concept and at least one check. Images need alt text; video needs captions.

### 6.2 Module and course builder (C-F04, UC-C-03)

Ordered modules of lessons and checks. A course adds outcomes, derived prerequisites from the graph, and course-level assessments. Drag-and-drop ordering; keyboard move buttons as the accessible primary (11 §14.3).

The **course** is the unit institutions assign and the unit that is released.

### 6.3 Learning path builder (C-F05, UC-C-04)

Ordered courses (and optional standalone modules or projects) toward a goal or role. The builder warns when a later course teaches a concept whose hard `prerequisite_of` is only taught by a still-later course. Example: a path that puts Deep Q-Networks before Q-Learning is invalid.

### 6.4 Curriculum builder

Programme-level outcomes mapped to courses. Not assigned to a cohort directly; institutions pick courses or paths. R2.

### 6.5 Quiz and item bank (C-F06, UC-C-05)

Items: type, difficulty, concept tags, Bloom level, answer key, rationale, locale variants. Authored templates live in `curriculum`; issued copies live in `assessment` and are created in the Instructor App. Keys stay on the server.

### 6.6 Challenge definitions

Author the definition (prompt, visible tests, hidden tests, reference solution). Scheduling and scoring stay in `gamification` (ADR 0013). Hidden tests never serialise to learner clients.

## 7. Taxonomy, graph, and metadata

Owned by `knowledge_steward`. Taxonomy is a tree for classification; the knowledge graph is typed relations for learning (13). They must not be edited as one structure.

**Graph editor** (`/knowledge/graph`): list or agenda view is the primary surface; the canvas is a map. Saving a `prerequisite_of` edge that would cycle is rejected. Example, left to right:

```text
bellman-equation  --prerequisite_of-->  q-learning
q-learning        --prerequisite_of-->  deep-q-networks
deep-q-networks   --prerequisite_of-->  advanced-rl
```

**Quality report** (`/knowledge/quality`): issues from 13 (orphans, difficulty inversion, cycles). Blocking issues stop a release.

**Metadata manager** (`/knowledge/metadata`, `/knowledge/vocabularies`): per-kind JSON Schema and controlled terms. Adding a resource type still needs a migration in v1; v2 vocabularies grow without a migration except for kind codes.

## 8. Review and publishing

States: `draft → in_review → approved → published → archived`. `changes_requested` is a transition back to `draft` with a required comment, not a stored state.

The reviewer cannot be an author of the version (two-person rule). In `master` the rule is mandatory. In an `org` workspace it is on by default; `org_admin` may turn it off.

Every transition emits `content.item.state_changed` and an audit row. `platform_admin` may take down published content in an emergency; that is not an edit.

## 9. Releases

Publishing a course or path creates an immutable release with semantic version `MAJOR.MINOR.PATCH` (ADR 0019). The publisher sees cohorts pinned to earlier releases and a change summary.

| Bump | When |
| --- | --- |
| MAJOR | Lesson or graded assessment removed; concepts or outcomes changed; order so progress cannot carry |
| MINOR | Lessons, checks, or locales added |
| PATCH | Text, media, or translation corrections |

PATCH advances pinned cohorts unless an assessment in the plan is open. MINOR and MAJOR need instructor adoption. Restoring a version creates a new release. Publishing emits `content.release.published`.

Instructors customise with overlays. Organisations with an `org` workspace may create a derived course; upstream releases appear as a reviewable diff. Master is never edited by a tenant.

## 10. AI generation

The generate page (C-F12, UC-C-10) drafts lesson notes, items, or summaries from published assets and the graph. Every draft records sources, model route, and prompt release. The draft stays in `draft` until a human reviews it. AI cannot publish and cannot write an answer key that skips review.

Grounding follows 13: generation that cannot cite a published asset version is refused or marked ungrounded and cannot enter `in_review`.

## 11. Localisation

Locales `en` (source and fallback), `fr`, `es`. Jobs per item and locale: `not_started → machine_draft → in_review → approved`, with `stale` when the source changes. A graded item is served in a locale only when `approved`. The English release is not blocked by a pending translation.

Editors work in `/localisation` with translation memory and glossary. UI strings of the Studio app itself live in `@aimentor/i18n`, not in this queue.

## 12. Analytics

Workspace-scoped: which lessons stall, which assets are opened, which graph edges correlate with drop-off. No learner-identifiable rows for authors who lack classroom roles. Platform-wide usage stays in the Admin App.

## 13. R1 and R2 split

| Release | What ships in Studio |
| --- | --- |
| **R1** | Split from `admin/`. Library, review queue, taxonomy, graph page, generate page, catalog import, Knowledge Pack seed into `master` as release `1.0.0` of each path. Workflow state rename `review` → `in_review`. `/content` aliases for today's `/admin` content routes |
| **R2** | Builders (lesson, course, path, items), 13 asset kinds with rights, typed weighted graph edits, metadata schemas, immutable releases, localisation jobs, content analytics |
| **R3** | Derived courses, org workspaces, overlay-aware impact analysis |

Until R1 lands, catalog and content screens remain on `admin :3001`. That is a holding pattern, not the product shape.

## 14. Open questions

| ID | Question | Owner |
| --- | --- | --- |
| CS-OQ-01 | Whether org workspaces may import Knowledge Pack records or only master may | Learning |
| CS-OQ-02 | Maximum concurrent AI generation jobs per author | AI admin |
| CS-OQ-03 | Whether challenge hidden tests are visible to `content_reviewer` or only `content_publisher` | Security |
