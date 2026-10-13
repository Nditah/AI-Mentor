# ADR 0009 — Knowledge repository design

- Status: Accepted (amended 2026-10-13)
- Date: 2026-10-13

## Context

The product teaches a fixed set of tracks: AI fundamentals, reinforcement learning, robotics, and LLM engineering. Lessons have prerequisites. Recommendations must refuse to jump a learner to PPO while the MDP lesson is unfinished. Authors also need a place for uploaded papers, which are a different kind of knowledge. See ADR 0007.

## Problem

Decide what the curriculum source of truth is, how prerequisites are stored, and how that differs from learner-uploaded documents.

## Decision

The authored curriculum has two layers:

1. `backend/app/domain/catalog.py` is the source the process trusts at runtime for concept names, prerequisites, lesson markdown, quiz templates, projects, and achievements.
2. Postgres holds the same courses, modules, lessons, concepts, relations, and path items so the dashboard, progress rows, and foreign keys have something to point at.

Startup seed upserts those rows from the catalog. It refreshes lesson markdown and does not delete lessons. Lesson slugs equal concept slugs, so completing `q-learning` and scoring `q-learning` are the same key.

Prerequisites are a directed graph. Recommendations use a stable topological order. A concept is eligible when its score is below 75 and every prerequisite is at or above 70. Missing prerequisites are reported rather than skipped.

Quiz items in the catalog include the answer key. The generate endpoint copies the key into `questions.answer_key` and returns only prompt, options, kind, and position. A model may add a coach note. It does not emit new keyed items.

Uploaded papers are `research_documents` and `document_chunks`. They are not lessons and they do not enter the prerequisite graph.

There is no instructor CMS in this build. An admin can list users and an instructor can read analytics. They cannot publish a new lesson through the API.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| A CMS as the only source on day one | The graph, the quiz keys, and the socratic openers would live in a tool that does not exist yet. A reviewable Python module ships with the tests. |
| Prerequisites only in the client | A modified client could request PPO first. Eligibility is computed on the server. |
| One blob of markdown per path with no concept ids | Mastery, flashcards, and quizzes would have nothing stable to attach to. |
| Mixing uploaded papers into the concept graph | A private PDF would become a prerequisite for other learners, and an untrusted file would enter the tutor’s curriculum. |

## Trade-off analysis

A catalog module is easy to test and awkward for non-developers to edit. That trade is accepted. Subject-matter edits are pull requests until a draft, review, and publish workflow exists. The seed step keeps Postgres aligned for learners who already have progress rows.

Duplication between the file and the tables can drift if a deploy runs old code against new rows or the reverse. Seed-on-startup makes the running code win for catalog fields it owns. Progress rows are keyed by lesson id, so renaming a slug is a migration, not a casual edit.

The graph is small enough to score in memory from the catalog. A graph database would add a service for a few dozen nodes.

Quiz templates cannot yet cover every concept at every difficulty. The generator says so and falls back to the items that exist, or returns 404 when the concept has none. It does not ask a model to write a key.

## Consequences

- Changing a concept means changing the catalog, adding a test when the rule changes, and letting seed upsert the row.
- Path detail returns lesson markdown and the prerequisite list to the signed-in learner.
- The public graph endpoint returns nodes and a Mermaid diagram. The studio also renders the same graph as a list.
- Research documents never satisfy a prerequisite.

## Future considerations

- Add an instructor workflow that writes a draft lesson, reviews it, and then exports into the catalog or replaces the seed for that slug.
- Version published lessons so a learner who started on revision A can finish it.
- Keep answer keys out of any future CMS payload that the browser can read.

## Amendment — 2026-10-13 hardening

The "no instructor CMS" statement above is superseded. The admin portal now has a curated library alongside the catalog:

- `knowledge_assets` move through `draft → review → approved → published → archived`, with every edit and transition snapshotted in `asset_versions` and audited.
- Only an admin publishes. Approval follows the four-eyes rule (AZ-5): the author may not approve or publish their own asset unless `CONTENT_SELF_APPROVAL` is on, and then the audit row is flagged `self_approved`.
- Each asset carries a licence from a fixed list (`own-work`, `cc-by`, `cc-by-sa`, `cc-by-nc`, `public-domain`, `proprietary-licensed`, `fair-use-excerpt`); anything else is rejected.
- Publishing indexes the asset into `knowledge_v1` for the tutor (ADR 0007). If the index is unavailable, publishing fails and the asset stays approved.
- Author references are `ON DELETE SET NULL`, so erasing a staff member keeps their published work.
- The catalog module is still the source for concepts, prerequisites, quiz keys, and socratic openers. Library assets do not enter the prerequisite graph. ADR 0019 describes the later Content Studio that unifies the two.
