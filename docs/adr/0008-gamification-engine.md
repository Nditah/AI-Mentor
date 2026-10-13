# ADR 0008 — Gamification engine

- Status: Accepted
- Date: 2026-10-13

## Context

The studio should feel like a practice loop: visible progress, a reason to return tomorrow, and a mastery picture that is not a single percentage pasted over the whole catalogue. The brief asked for XP, levels, badges, streaks, leaderboards, and either FSRS or SM-2.

## Problem

Choose rules that reward evidence of learning, resist farming, and schedule reviews with an algorithm the team can test by hand.

## Decision

Gamification is a pure domain policy in `app/domain/gamification.py` and `app/domain/scheduling.py`. The service persists the result.

| Rule | Value |
| --- | --- |
| Level | `1 + xp // 250` |
| Daily XP cap | 400 |
| Lesson complete | 40 |
| Flashcard review | 5 |
| Lab status `ok` | 25 |
| Research analysis | 20 |
| Quiz | `10 + round(40 * ratio)` |
| Chat | Streak updates. XP stays 0 |

A streak increments on consecutive calendar days and resets to 1 after a gap. The same day does not increment twice.

Mastery is 0–100 and is renormalised over the evidence that exists: quizzes 0.45, lessons 0.25 when a lesson exists and the learner has engaged, projects 0.20 when a project was attempted, recall 0.10. Bands are strength at or above 75, developing at or above 60, gap above 0, otherwise unstarted. Recommendations skip scores at or above 75 and require prerequisites at or above 70. A learner with no evidence is pointed at the roots, AI Fundamentals and Python, rather than at PPO.

Flashcard scheduling is Anki SM-2 behind a `Scheduler` protocol. Quality below 3 resets repetitions and the interval and leaves ease unchanged. Success uses intervals of 1 day, then 6, then `ceil(interval * ease)`, with ease floored at 1.3. The studio maps Again, Hard, Good, and Easy to qualities 1, 3, 4, and 5.

Badges are derived from counters: first lesson, streaks, a perfect quiz, mastery, a review, and code that passed. The leaderboard exposes display name, XP, level, and streak.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| FSRS in this release | A half-implemented FSRS silently ruins intervals. The protocol can host a tested FSRS later. |
| XP for every chat message | Farming. Chat is the cheapest action and the least evidence. |
| One mastery number for the account | Hides whether the learner can do Q-learning or has only opened a lesson. |
| A third-party gamification SaaS | The rules are teaching policy. They belong next to the grader and the graph. |

## Trade-off analysis

Deterministic rules are easy to test and easy to explain. They are also coarse. A short quiz and a long quiz can move mastery by similar weights because the quiz ratio is what enters the evidence, not the item count. That is acceptable while quizzes are short authored sets.

SM-2 is well known and slightly blunt for learners who use Again and Easy in long runs. The ease floor of 1.3 stops intervals from collapsing to zero. FSRS would fit review history better after its implementation is compared with SM-2 on the same traces.

The daily cap stops a script from minting levels. It also caps a legitimate long study day. Four hundred XP is a bit more than one level. That is the intended ceiling.

Streaks use the server date. A learner near midnight can lose a day. The rule stays simple until a timezone is stored on the user.

## Consequences

- XP grants go through `award_amount` and append an `xp_events` row.
- Mastery is recomputed for the concept after a quiz, a lesson, a passing submission, or a review. It is not a stored running average the client can edit.
- The dashboard read model groups concepts into strengths, developing, and gaps.
- Leaderboard queries must keep selecting only the public columns.

## Future considerations

- Implement FSRS beside SM-2 and switch with a per-deck flag after the intervals match published vectors.
- Store a learner timezone before streak fairness becomes a support issue.
- Add country boards only with an explicit country field. The current leaderboard is global and minimal.
