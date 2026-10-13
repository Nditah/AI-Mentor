# ADR 0023 — Localisation architecture for UI, content, AI, assessments, and reports

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13

## Context

The v1 apps are English only. The ADR 0011 DDL already prepares content localisation: `ref.languages`, `identity.user_profiles.preferred_locale` (default `en`), `curriculum.concept_translations` and `question_translations` with `translation_source` (`human` or `machine`) and reviewer, and one published lesson body per lesson, locale, and teaching style. ADR 0011 rejected forking lesson rows per language because that would fork learner progress.

The v2 direction requires English, French, and Spanish across five surfaces: UI, learning content, AI responses, assessments, and reports. Institutions in Francophone and Hispanophone markets will set a default locale for their members.

## Problem

Decide how each surface is localised, how a person's locale is chosen, how translations are produced and reviewed, and what happens when a translation is missing.

## Decision

**Locales.** `en` (default and fallback), `fr`, `es`. Locale codes are BCP 47 language tags without region in R1–R3. A region variant (`es-MX`) may be added later as a fallback chain `es-MX → es → en`.

**Locale resolution** for a request, first match wins: explicit learner choice (`preferred_locale`); organisation default (`tenancy.org_policies.default_locale`) for members who have not chosen; `Accept-Language`; `en`. The resolved locale is sent as `Content-Language` and recorded on sessions.

| Surface | Mechanism | Missing translation |
| --- | --- | --- |
| UI | `next-intl` in every app via `packages/i18n`, ICU MessageFormat catalogues per app plus a shared catalogue; keys are stable ids, never English strings | Fall back to `en` string; CI fails if a released app has missing keys for any supported locale |
| Learning content | Per-locale bodies for lessons, concepts, questions, paths; translation jobs in Content Studio | Show `en` body with a "not yet available in your language" notice |
| AI responses | The tutor answers in the session locale; the prompt states the locale; a language-identification check runs on each reply | Regenerate once if the reply language differs; then return with a notice |
| Assessments | Graded items need `translation_status = approved` in the learner's locale | Item is not offered in that locale; the assignment shows only locales where every item is approved |
| Reports | Rendered per recipient locale at send time, with locale-aware numbers, dates, and plural rules | `en` |

**Translation workflow.** Content Studio creates a translation job per item and target locale. Machine translation (through `ai_gateway`) produces a draft with `translation_source = machine`. A `localisation_editor` for that locale reviews it; approval sets `translation_status = approved` and `translation_source = human` if edited. Translations follow the same workflow states as their source ([ADR 0019](0019-content-studio-releases.md)). A release lists, per locale, whether it is complete.

**Translation memory and glossary.** The `i18n` module stores approved segment pairs and a per-locale glossary of controlled terms (for example "Q-learning" is not translated; "reward" is "récompense" and "recompensa"). Machine drafts are pre-filled from memory and constrained by the glossary.

**Locale-neutral identity.** Concepts, lessons, items, and badges have one id across locales. Progress, mastery, XP, and grades attach to that id, so changing language never resets progress. A learner who starts in `fr` and switches to `en` keeps every record.

**Formatting.** Dates, numbers, and currency use ICU through `Intl` in the browser and Babel in Python. Times are stored in UTC and rendered in the person's time zone.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Separate lesson rows per language | Forks progress and mastery per locale; rejected in ADR 0011. |
| `react-i18next` | Works, but `next-intl` integrates with App Router server components and routing with less configuration. |
| Machine translation at request time | Unreviewed text in graded assessments is unfair; cost and latency on every read. |
| Third-party TMS (Crowdin, Lokalise) as the content store | Acceptable for UI catalogues later; content translations need the content workflow, rights, and releases inside the database. |
| Let the model answer in whatever language the learner typed | Learners mix languages; responses must follow the declared locale so assessments and reports stay consistent. |

## Trade-off analysis

Reviewed translations for graded items slow the availability of new assessments in `fr` and `es`. The alternative, grading learners on unreviewed text, is a fairness defect. Practice items may use machine drafts with a visible label.

A language check per AI reply adds about 5 ms with a local language-identification model. It catches the common failure where retrieved English chunks pull the reply into English.

## Consequences

- Every user-visible string in the five apps goes through `packages/i18n`. Lint rejects JSX string literals outside tests.
- Notification templates (`notification.templates`) are per locale.
- Search indexes each locale separately with the matching analyser.
- [11-ux-specification.md](../platform/11-ux-specification.md) covers text expansion (French and Spanish run about 20 to 30 percent longer than English).

## Future considerations

- Right-to-left support (Arabic) requires logical CSS properties throughout; `packages/ui` adopts them from R1 to keep the option cheap.
- Additional locales (`pt`, `de`, `ar`, `sw`) are added by catalogue and editor capacity, not by code changes.
