# ADR 0013 — Five applications on one shared platform

- Status: Accepted (five apps live in `apps/`; API audiences, tenancy, and `/content` `/platform` roots still follow the roadmap)
- Date: 2026-10-13
- Amends: [ADR 0001](0001-nextjs-studio.md) (the learner frontend is no longer called "studio"), [ADR 0012](0012-separate-admin-app.md) (the admin portal splits in two)

## Context

Today there are two frontends. `frontend/` is the learner app, called "the studio" in v1 documents and in its `(studio)` route group. `admin/` is the staff portal with thirteen route groups: analytics, audit, challenges, configuration, curriculum, generate, graph, library, moderation, providers, review, taxonomy, and users. Roles are a linear rank (`student < instructor < admin`) in `backend/app/domain/access.py`.

The product direction in [docs/platform/README.md](../platform/README.md) adds instructors who teach cohorts, institutions that buy licences and run reporting, and a content team that governs a master repository. Those groups have different navigation, density, session rules, and release timing. Putting them all in the staff portal would recreate the problem ADR 0012 solved for learners and staff. The word "studio" also collides: it means the learner app in v1 and the content tool in v2.

## Problem

Decide how many frontend applications the platform has, what each one owns, where it is deployed, and how a person who belongs to several user groups moves between them.

## Decision

AI Mentor has five Next.js applications on one API. Each is its own Vercel project, its own origin, and its own Clerk authorised party (`azp`).

| App | Code name | Origin | Source | Local port |
| --- | --- | --- | --- | --- |
| Learner App | `learner` | `learn.<domain>` (marketing at `<domain>`) | `apps/learner` | 3000 |
| Admin App | `admin` | `admin.<domain>` | `apps/admin` | 3001 |
| Instructor App | `instructor` | `teach.<domain>` | `apps/instructor` | 3002 |
| Institution App | `institution` | `org.<domain>` | `apps/institution` | 3003 |
| Content Studio | `studio` | `studio.<domain>` | `apps/studio` | 3004 |

The current `admin/` routes split as follows:

| Goes to | Routes |
| --- | --- |
| Admin App | `users`, `configuration`, `providers`, `audit`, `moderation`, `analytics` |
| Content Studio | `library`, `review`, `curriculum`, `taxonomy`, `graph`, `generate`, `challenges` (authoring of challenge definitions; scheduling and scoring stay in the gamification service) |

Rules:

1. "Studio" means Content Studio only. The learner frontend is the "Learner App". The `(studio)` route group in `frontend/app` is renamed when the code moves to `apps/learner` (R1).
2. One Clerk production instance serves all five subdomains, so one sign-in opens every app the person may use.
3. Every app shows an app launcher fed by `GET /api/v1/me/apps`, which lists only the apps the person's role assignments open ([ADR 0016](0016-scoped-rbac-abac.md)).
4. The API enforces every permission. An app's route guard decides only what to render.
5. API roots carry an app audience. The API reads `azp` from the session token and rejects a request whose root is not allowed for that origin:

| API root | Accepted `azp` |
| --- | --- |
| `/api/v1/me/...` | all five apps |
| `/api/v1/learn/...` | Learner App |
| `/api/v1/orgs/{org_id}/...` | Instructor App, Institution App |
| `/api/v1/content/...` | Content Studio |
| `/api/v1/platform/...` | Admin App, with MFA verified within the last 15 minutes (`fva`) for writes |

6. Each app has its own content security policy and `X-Robots-Tag`. Only the Learner App and the marketing site are indexable.
7. The v1 `/api/v1/admin/*` routes are retired in R2, after their operations move to `/platform` and `/content`.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| One app with role-based sections | Every release ships every audience. Instructor gradebooks and answer keys would sit in the learner bundle. A single CSP and session lifetime cannot fit both a 13-year-old learner and a platform admin. |
| Keep `admin/` as one staff app for admins, content teams, and instructors | Content authoring, platform operations, and classroom teaching have no shared navigation. Instructors are customers, not staff, and need institution branding. |
| Three apps (learner, staff, institution) | Content Studio has its own workflow, editors, and release cadence (R2), and its users are a different group from platform operators. Combining them keeps the problem ADR 0012 started to solve. |
| Path-based apps on one origin (`/teach`, `/org`) | Shared cookies and CSP, and a broken deploy at one path can take down the others. |

## Trade-off analysis

Five apps cost five Vercel projects, five CI jobs, five sets of environment variables, and five CSPs. The monorepo in [ADR 0014](0014-monorepo-shared-packages.md) keeps that cost down: shared packages, one lockfile, and CI that builds only affected apps.

Splitting by user group rather than by feature means some screens look alike across apps (an analytics chart in the Institution App and the Admin App). They share components from `packages/ui`; they do not share routes. The cost is two thin pages calling different API roots with different scopes.

App audiences add a second check beside permissions. That is deliberate: a stolen Learner App session cannot call `/platform` even if the person is a platform admin.

## Consequences

- The five Next.js apps live under `apps/`. `GET /api/v1/me/apps` feeds the launcher. Instructor and Institution screens that need tenancy show empty organisation queues until `/orgs/{org_id}` lands. Shared packages (ADR 0014) are not extracted yet.
- `CORS_ORIGINS` lists all five origins. Stripe return URLs are validated against a Learner App and Institution App list only (closes the ADR 0012 future consideration).
- The API settings gain an `APP_AUDIENCES` map from `azp` to code name. A request with an unknown `azp` is rejected with 401.
- v1 documents that say "studio" for the learner app are read as "Learner App".

## Future considerations

- Native mobile clients become additional authorised parties with the Learner App audience ([ADR 0027](0027-extension-points.md)).
- White-label domains for institutions (R4) map a custom domain to the Learner App and Institution App with the organisation's branding; they do not create new apps.
