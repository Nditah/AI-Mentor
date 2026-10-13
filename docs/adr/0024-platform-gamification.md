# ADR 0024 — Platform-wide gamification with scoped leaderboards

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13
- Amends: [ADR 0008](0008-gamification-engine.md) (gamification becomes a platform service; leaderboards gain scopes)

## Context

ADR 0008 makes XP, levels, streaks, and badges a deterministic domain policy: level `1 + xp // 250`, a 400 XP daily cap, fixed grants per activity, and one global leaderboard showing display name, XP, level, and streak. ADR 0011's DDL adds `game.xp_ledger`, `game.user_stats`, `game.challenges`, `game.leaderboards` with scopes `global`, `country`, `region`, and computes friends rankings on read.

The v2 direction asks for gamification across the platform: points, achievements, titles, competitions, and daily, weekly, and seasonal challenges; leaderboards for global top 10, country top 10, institution, cohort, and friends; and rank, percentile, XP, achievements, and streaks for each learner. Institutions want cohort competitions but also control over whether their learners appear publicly.

## Problem

Decide where gamification lives, how XP relates to tenants, how scoped leaderboards are computed and served, and how the system resists abuse.

## Decision

**Service.** The `gamification` module ([ADR 0017](0017-bounded-contexts-platform-services.md)) owns the `game` schema. It reacts to events (`learning.lesson.completed`, `learning.mastery.changed`, `assessment.grade.released`, practice events) and publishes `gamification.xp.awarded`, `gamification.badge.earned`, and `gamification.level.reached`. The ADR 0008 rules are kept as the default rule set; quiz grants, lesson grants, and the daily cap remain unchanged.

**XP ledger.** `game.xp_ledger` is person-level and append-only, with `tenant_id` of the context the XP was earned in and an idempotency key `(source_event_id, rule_id)`. A person has one level and one streak across tenants. Organisation views sum only rows with their `tenant_id` and respect [ADR 0021](0021-learner-record-ownership.md) consent.

**Rules, not grants.** XP and badges come only from configured rules evaluated on events. Instructors cannot award XP directly. An organisation admin may enable bounded rule variants for its tenant (for example a cohort challenge bonus of up to 100 XP), and every variant counts toward the daily cap.

**Leaderboard scopes.** `ref.leaderboard_scope` becomes `global`, `country`, `organisation`, `cohort`, `friends` (v1 `region` is dropped until a region field exists). `game.leaderboard_scopes` registers each board instance: scope type, scope key (country code, organisation id, or cohort id), visibility, and whether names or pseudonyms are shown.

| Scope | Members | Shown | Default visibility |
| --- | --- | --- | --- |
| `global` | All opted-in learners | Top 10 plus the viewer's rank and percentile | Pseudonymous display name; guests see the top 10 |
| `country` | Opted-in learners with `country_code` set | Top 10 plus viewer | Same as global |
| `organisation` | Active members of one tenant | Top 50 plus viewer | Members of that organisation only |
| `cohort` | Members of one cohort | Full list | Cohort members and staff |
| `friends` | Accepted `game.friendships` | Full list | The viewer |

Periods: `weekly` (Monday 00:00 UTC), `monthly`, `season`, `all_time`. A season is a calendar quarter. The v1 `daily` period is not offered as a board; daily activity stays in challenges and streaks. Metric defaults to XP earned in the period.

**Organisation opt-out.** An organisation may exclude its managed learners from `global` and `country` boards (policy `leaderboards.public_participation`, default off for every organisation kind; an organisation may turn it on). Personal-account members decide for themselves. Learners aged 16–17 are excluded from `global` and `country` boards regardless, and the platform has no accounts under 16.

**Serving.** Redis sorted sets hold live ranks, one key per board: `lb:<scope>:<scope_key>:<period>:<period_start>`. XP events update the sets with `ZINCRBY`. Rank is `ZREVRANK`; percentile is `100 * (1 - rank / count)`. Each period close writes a frozen snapshot to `game.leaderboards` and `game.leaderboard_entries` (`status = closed`) so history and badges do not depend on Redis. Friends boards are computed on read by intersecting the friend set with the global set.

**Competitions and challenges.** `game.competitions` (organisation or cohort scoped, with start, end, rule set, and team option) and `game.seasons` are new tables. Daily and weekly challenges continue in `game.challenges`. Challenge definitions are authored in Content Studio; scheduling and scoring stay here.

**Anti-abuse.** Daily cap; idempotent grants; minimum time-on-task before lesson XP; no XP for chat (ADR 0008); quiz XP only on the first attempt per item per day; anomaly flags (XP rate above the 99.9th percentile, repeated identical submissions) hold grants for review; flagged learners are hidden from public boards until cleared.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Separate XP per tenant | A learner's level would reset on joining a cohort, and streaks would split. |
| Instructor-awarded XP | Inflation and favouritism; undermines comparability across cohorts. |
| Compute ranks with SQL window functions on read | Fine at thousands of learners; at 100,000 daily learners the global board recomputes on every view. ADR 0011 already deferred this to Redis. |
| Public boards by default for every learner | Children and employees must not be ranked publicly without a decision by their organisation or themselves. |

## Trade-off analysis

Redis adds a second store whose data can be rebuilt from the ledger (a rebuild job replays the period's `xp_ledger` rows). Losing Redis degrades boards to the last snapshot; it never loses XP.

Person-level XP with tenant context makes organisation views a filtered sum rather than a separate counter. That is cheaper to keep correct and slightly more expensive to read; organisation boards are cached for 60 seconds.

## Consequences

- R1 keeps ADR 0008 behaviour and adds `tenant_id` to `xp_ledger`. Scoped boards arrive with the Instructor and Institution Apps (R3); global and country boards with R2.
- Leaderboard responses still exclude email and real names unless the viewer is in the same cohort and the organisation allows names.
- The Admin App shows held grants and anomaly flags.

## Future considerations

- Team competitions across organisations (inter-university leagues) with explicit consent from each organisation.
- Learner time zones for streaks (ADR 0008 future consideration) before seasonal streak challenges launch.
