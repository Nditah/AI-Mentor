# ADR 0014 — Monorepo with shared front-end packages

- Status: Accepted (apps live under `apps/`; shared packages and the single lockfile are not extracted yet)
- Date: 2026-10-13

## Context

The repository has two frontends, `frontend/` and `admin/`, each with its own `package.json` and `package-lock.json`. ADR 0012 copies Tailwind tokens and primitives between them and asks that a token change land in both files in the same change. It already names three packages to extract: `packages/ui`, `packages/content-render`, and `packages/api-client`.

[ADR 0013](0013-five-applications-shared-platform.md) raises the frontend count to five. Five copies of the theme, the Markdown renderer, the Clerk setup, and the API types would drift within weeks.

## Problem

Choose a repository layout and build tooling that let five apps share code, keep one dependency graph, and build only what changed.

## Decision

The frontends move into one npm workspace with Turborepo. The backend stays in `backend/`.

```text
apps/
  learner/       Learner App (from frontend/)
  instructor/    Instructor App (new, R3)
  institution/   Institution App (new, R3)
  admin/         Admin App (from admin/)
  studio/        Content Studio (from admin/)
packages/
  ui/                Tailwind preset, theme tokens, primitives, DataTable, app launcher
  content-render/    Markdown, KaTeX, Mermaid (securityLevel "strict"), code blocks, .prose-mentor styles
  api-client/        Types and typed fetchers generated from docs/openapi.yaml
  auth/              Clerk provider setup, token forwarding, app-audience helpers, route guards
  i18n/              next-intl setup, locale negotiation, shared message catalogues (ADR 0023)
  config/            Shared tsconfig, ESLint, Prettier, Tailwind base, Next.js config helpers
  analytics-client/  Typed product-analytics events and the browser emitter
backend/             FastAPI modular monolith (unchanged location)
```

Rules:

1. One root `package.json` with `"workspaces": ["apps/*", "packages/*"]` and one root `package-lock.json`. The per-app lockfiles are deleted. npm stays the package manager, because both existing apps already use npm lockfiles.
2. Packages are internal (`"private": true`), named `@aimentor/<name>`, and consumed as TypeScript source through Next.js `transpilePackages`. They are not published.
3. Dependency direction: apps import packages; packages never import apps. `ui` and `content-render` do not import `api-client` or `auth`. An ESLint boundary rule enforces this.
4. `packages/api-client` is regenerated from `docs/openapi.yaml` by `npm run generate -w @aimentor/api-client`. CI fails if the generated output differs from the committed output.
5. Turborepo runs `lint`, `typecheck`, `test`, and `build`. CI uses `turbo run <task> --filter=...[origin/main]` so a change to `packages/ui` builds all five apps, and a change to `apps/studio` builds only the Studio.
6. Each Vercel project sets its root directory to `apps/<name>` and uses an ignored-build step that skips the deploy when Turborepo reports the app unaffected.
7. Adding a third-party UI dependency to any app still follows the allow-list in ADR 0012. A dependency used by two or more apps moves into a package.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Separate repositories per app | Shared packages would need publishing and versioning. A token change becomes five pull requests. |
| Keep top-level `frontend/` and `admin/` and add more folders | No shared lockfile or task graph. Every app re-implements the same CI job. |
| pnpm workspaces | Faster installs and stricter hoisting, but a tooling change on top of a layout change. npm workspaces are sufficient at five apps. Revisit if install time becomes a CI cost. |
| Nx | More capable generators and boundary rules than needed. Turborepo does task caching and affected builds with one config file. |
| Move the backend into `apps/api` | Python tooling (uv, pytest, Alembic, Docker build context) does not benefit from a JavaScript task graph. The backend keeps its own CI job. |

## Trade-off analysis

One lockfile means one upgrade for React or Next.js across all apps. That is the goal, and also the risk: a breaking upgrade blocks all five until each is fixed. Upgrades land on a branch with all five builds green.

Source-consumed packages avoid a build step for packages but make every app's build compile them. Turborepo's cache keeps that cheap. Remote caching on Vercel is enabled for CI.

## Consequences

- R1 performs the move with `git mv` so history is kept. `make web` becomes `make learner`; `make admin` stays; `make studio`, `make instructor`, and `make institution` are added as each app arrives.
- `frontend/Dockerfile` moves to `apps/learner/Dockerfile` and builds from the repository root with `turbo prune`.
- ADR 0012's rule that tokens are copied between two Tailwind configs ends: tokens live only in `packages/ui`.
- The lesson preview in Content Studio and the lesson page in the Learner App render through the same `packages/content-render` component.

## Future considerations

- A `packages/mobile-shared` package for React Native clients if they reuse API client and i18n code ([ADR 0027](0027-extension-points.md)).
- A `packages/events` package generated from `docs/events/*.json` if frontends start consuming domain event types ([ADR 0018](0018-event-outbox.md)).
