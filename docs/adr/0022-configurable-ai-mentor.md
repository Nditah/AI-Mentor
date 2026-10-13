# ADR 0022 — Configurable AI mentor: modes and personas as policy profiles

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13
- Amends: [ADR 0010](0010-ai-tutor-architecture.md) (specialist agents become modes; `socratic` and `direct` become a technique inside `tutor`)

## Context

ADR 0010 has one tutor with specialist agents (tutor, quiz, research, coding, planner, career) selected by intent classification. The teaching decision lives in `app/domain/socratic.py`; agents only phrase a `TurnPlan`. Learners choose `socratic` or `direct`. ADR 0011's DDL already has `identity.tutor_avatars`, `ref.voice_accents`, and learning preferences.

The v2 direction asks for a configurable mentor: personality, teaching style, voice style, age appearance, gender presentation, accent, and coaching style; and six modes (Tutor, Mentor, Research Supervisor, Coding Coach, Career Coach, Exam Coach). Institutions need to restrict the mentor during graded work, and a school may not want a career coach for 12-year-olds.

## Problem

Decide what a mode is, what a persona may and may not change, who can restrict them, and how the mentor stays honest about being an AI.

## Decision

**Modes** are the job the AI is doing. Each mode is an agent plus a policy profile, released through `platform.prompt_releases` by `ai_admin` holders ([ADR 0017](0017-bounded-contexts-platform-services.md), `ai_gateway`).

| Mode | Agent | Policy profile highlights |
| --- | --- | --- |
| `tutor` | Tutor | Technique setting `socratic` (default) or `direct`; ADR 0010 stages 0 and 1 stay scripted; grounded in the pinned release |
| `mentor` | Mentor | Goal setting, reflection, study habits; no new content claims without citations |
| `research_supervisor` | Research | Critique must cite a chunk (ADR 0007); questions capped as in ADR 0010; never writes the learner's paper |
| `coding_coach` | Coding | Narrates deterministic review notes; never executes code; hints before solutions |
| `career_coach` | Career | Role matches from the deterministic scorer; no claims about salaries or hiring outcomes without a cited source |
| `exam_coach` | Exam | Revision plans and practice from practice items only; never sees items from an open assessment |

A policy profile is data: allowed tools, grounding requirement (`release_only`, `release_and_uploads`, `open_with_citations`), solution disclosure (`never`, `after_attempts:<n>`, `allowed`), maximum response length, safety prompt version, and evaluation suite id. The engine applies it before any model call; the model never selects its own profile.

**Personas** are how the AI presents, stored in `personalisation.mentor_personas`:

| Field | Values (examples) |
| --- | --- |
| Personality | warm, calm, energetic, matter-of-fact |
| Teaching style | maps to the `approach` dimension (storytelling to mathematical) |
| Coaching style | encouraging, challenging, structured |
| Voice style | TTS voice id per locale |
| Accent preference | from `ref.voice_accents` |
| Age appearance | young adult, adult, senior |
| Gender presentation | feminine, masculine, neutral |

A persona never changes correctness, grounding, safety rules, grading, or mode policy. It changes wording, tone, examples, avatar, and voice. Evaluation suites run each mode against at least three personas and fail if factual or safety scores differ by more than 2 percentage points.

**Voice.** Each persona maps to one TTS voice per locale (`en`, `fr`, `es`) through `ai_gateway`. If the locale has no voice for that persona, the nearest persona voice is used and the UI says so.

**Restriction.** Organisation policy (`tenancy.org_policies`) and cohort settings may disable modes, bound persona options (for example only `neutral` gender presentation, no avatar), and bound dimensions. The effective configuration is the intersection of platform, organisation, cohort, and learner choices; the most restrictive wins.

**Assessment integrity mode.** While a learner has an open graded assessment with integrity on, `exam_coach` is disabled, solution disclosure is `never` for every mode, and the tutor refuses questions about concepts tagged on that assessment, stating why. The state is a context attribute in the policy engine ([ADR 0016](0016-scoped-rbac-abac.md)).

**Disclosure.** The mentor is always presented as an AI. Avatars are illustrated or stylised, never photorealistic human likenesses, and voices are not cloned from real people. Each session start and every voice session shows an AI disclosure. A persona cannot claim human experiences or credentials.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| One generic assistant with a style prompt | No place to enforce mode-specific rules such as "exam coach never sees open items". |
| Personas that change teaching rules (a "strict" persona that grades harder) | Grades would depend on presentation choices. Personas must be cosmetic for fairness. |
| Photorealistic avatars and cloned voices | Risk of deception and of minors forming misplaced trust; conflicts with EU AI Act transparency duties for systems interacting with people. |
| Learner-only configuration | Institutions could not meet assessment integrity or age-appropriateness duties. |

## Trade-off analysis

Treating modes as policy profiles keeps behaviour testable and released like code, at the cost of slower experimentation: a new mode needs an agent, a profile, and an evaluation suite. Persona breadth multiplies evaluation cost; three personas per mode is the floor that keeps the suite affordable.

## Consequences

- The v1 `socratic`/`direct` choice becomes `tutor` technique; v1 intent routing selects a mode suggestion the learner confirms.
- `tutor.message.flagged` events feed the Admin moderation queue for every mode.
- [11-ux-specification.md](../platform/11-ux-specification.md) defines the mentor configuration screens.

## Future considerations

- Real-time voice conversation once TTS and speech recognition latency is under 800 ms round trip.
- Agent orchestration across modes on the learner's behalf ([ADR 0027](0027-extension-points.md)).
