# ADR 0025 — Assessment platform with AI-assisted marking and human override

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13

## Context

v1 grading is deterministic and practice-only: quiz answer keys come from the catalog, the model may add a coach note but never a key (ADR 0009), research questions are capped at 0.70, and the code runner checks submissions (ADR 0010). The ADR 0011 DDL has `curriculum.assessments` and `learning.quiz_attempts` for practice.

Institutions need formal assessment: exams, assignments, projects, coding assessments, and written responses, marked against rubrics, often with open-ended answers that a deterministic grader cannot score. Instructors want AI help with marking volume, and must be able to review open-ended responses and override AI grades.

The EU AI Act lists AI systems used to evaluate learning outcomes in education (Annex III, point 3) as high-risk. Deployers and providers of such systems need human oversight, logging, transparency to affected persons, accuracy monitoring, and data governance.

## Problem

Decide how formal assessment differs from practice, how AI participates in marking, who decides a grade, when grades reach learners, and how the design meets high-risk obligations.

## Decision

**Separation.** Practice (quizzes, flashcards, daily challenges, coding lab) stays in `learning` and feeds mastery and XP. Formal assessment lives in the `assessment` module and schema (`assessments`, `assessment_items`, `assignments`, `rubrics`, `rubric_criteria`, `rubric_levels`, `submissions`, `submission_responses`, `marks`, `ai_mark_proposals`, `grades`, `grade_overrides`, `accommodations`). Practice items and formal items are separate pools; an item in an open assessment is never served as practice or to the exam coach ([ADR 0022](0022-configurable-ai-mentor.md)).

**Marking paths.**

| Item type | Marked by | Released |
| --- | --- | --- |
| Objective (single or multiple choice, numeric, exact match, unit-tested code) | Deterministic grader | May auto-release if the assignment enables it |
| Open-ended (written response, essay, project, proof, code quality) | Rubric, by a human, optionally with an AI proposal | Only after a human accepts or overrides |

**AI-assisted marking.** When enabled (`instructor.ai_marking` flag and organisation policy), the `assessment` module asks `ai_gateway` for a proposal per submission. An `ai_mark_proposals` row holds, per rubric criterion: proposed level, score, rationale, quoted evidence spans from the response, and a confidence from 0 to 1, plus model id, prompt release, and rubric version. Proposals are never visible to the learner. A marker with `assessment.submission:mark` sees the proposal beside the response and accepts, edits, or rejects each criterion. An edit or rejection is a `grade_overrides` row with a required reason. Proposals with confidence below 0.6 are shown as "low confidence" and are not pre-selected.

**Moderation sampling.** For each assignment, at least 10 percent of AI-accepted marks (minimum 5, all if fewer than 5) are routed to a second marker. Disagreement above one rubric level on any criterion sends the whole batch to review. Instructors can also sample by learner group to check for bias.

**Grade release.** Grades become visible only through `assessment.grade:release` by an instructor (or a TA if delegated), per assignment or per learner. Release publishes `assessment.grade.released`. Overrides after release publish `assessment.grade.overridden` and notify the learner. Organisation policy may require `lead_instructor` approval for overrides after release.

**Integrity.** During an open assignment with integrity mode on, the mentor is restricted (ADR 0022), item order and options may be shuffled per learner, and attempts and time limits are enforced on the server. Accommodations (extra time, extra attempts) are per learner and audited.

**High-risk controls** (EU AI Act Annex III, point 3):

| Obligation | Control |
| --- | --- |
| Human oversight | No AI proposal becomes a grade without a human decision; markers can disable AI per assignment |
| Logging | Every proposal, decision, and override is retained with model, prompt, rubric versions for the academic record's retention period |
| Transparency | Learners are told when AI assisted the marking of their work and can request human re-marking |
| Accuracy and bias | Per-rubric agreement between AI and human marks is tracked; an `ai_admin` evaluation gate blocks a prompt release whose agreement drops below 0.8 quadratic weighted kappa on the reference set |
| Data governance | Submissions are not used to train models; provider contracts disable retention |

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Reuse practice quizzes as assessments | Practice items are seen repeatedly and feed the tutor; a formal item must stay unseen and controlled. |
| Fully automatic AI grading | High-risk under the AI Act without human oversight, and instructors remain accountable for grades. |
| No AI marking | Instructors with 200 essays get no help; AI-assisted marking is a core v2 capability. |
| Show proposals to learners before review | Learners would contest drafts; proposals are marker aids, not grades. |

## Trade-off analysis

Human acceptance of every open-ended mark keeps instructors in the loop and caps the time saving at reading-and-confirming speed (target: 50 percent faster than unassisted marking). Moderation sampling costs a second marker's time on 10 percent of work; it is the main evidence that AI-assisted marks are reliable.

## Consequences

- Assessment ships in R3 with the Instructor App. Objective auto-grading ships first; AI-assisted marking behind `instructor.ai_marking`.
- The v1 `curriculum.assessments` table becomes the practice assessment definition or is migrated into `assessment.assessments`; [07-database-design.md](../platform/07-database-design.md) decides.
- A conformity and fundamental-rights impact assessment is completed before AI marking is enabled for any EU organisation.

## Future considerations

- QTI 3.0 import and export of items (R4 or later, [ADR 0026](0026-interoperability-standards.md)).
- Proctoring integrations are out of scope until an organisation requires them; they would be integrations, not built in.
