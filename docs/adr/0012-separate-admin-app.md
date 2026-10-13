# ADR 0012 — Separate admin app, one design system

- Status: Accepted (amended 2026-10-13)
- Date: 2026-10-13
- Amends: [ADR 0001](0001-nextjs-studio.md) (the studio no longer hosts admin screens)

## Context

The studio serves learners. The admin portal serves instructors and admins: the knowledge library, review queue, curriculum builder, taxonomy and graph editors, AI generation, moderation, users, configuration, and audit. The two audiences need different navigation, density, session rules, and release timing. Staff accounts are high-value targets, and the admin screens handle answer keys, drafts, and learner records that must never ship in the learner bundle.

An earlier recommendation put the portal inside the studio as a `/admin` route group. This record replaces it.

The team is small. Every extra framework is another upgrade path, another set of accessibility checks, and another idiom in code review.

## Problem

Decide whether the admin portal is part of the studio or its own application, and which UI stack it uses.

## Decision

The admin portal is a separate Next.js application in `admin/`, deployed as its own Vercel project at `admin.<domain>` (port 3001 locally, `make admin`). It deploys and releases independently of the studio.

Both apps use one stack and one design system:

| Layer | Studio and admin |
| --- | --- |
| Framework | Next.js 15 App Router, React 19, TypeScript |
| Styling | Tailwind CSS 3 with the same theme tokens (colours, fonts, radii, shadows, dark mode by class) |
| Components | shadcn/ui pattern: local primitives built with `class-variance-authority`, `clsx`, `tailwind-merge`, Radix primitives where a widget needs them |
| Icons | `lucide-react` |
| Server state | TanStack Query |
| Identity | Clerk, one production instance for both subdomains |
| Content rendering | `react-markdown`, `remark-gfm`, `remark-math`, `rehype-katex`, Mermaid with `securityLevel: "strict"` |

The admin app may add only these, each on the screens that need it, loaded lazily where the bundle is large:

| Need | Library |
| --- | --- |
| Tables (library, review queue, users, audit) | TanStack Table, TanStack Virtual |
| Forms (asset metadata, configuration) | React Hook Form, Zod |
| Lesson editor | CodeMirror 6 (Markdown) |
| Version diff | Monaco diff editor |
| Knowledge-graph editor | React Flow (`@xyflow/react`) |
| Curriculum builder | dnd-kit |
| Taxonomy tree | react-arborist |
| Charts | Recharts through shadcn chart primitives |

Not used in either app: MUI or any CSS-in-JS library, a second component kit, Refine or react-admin, low-code admin builders, and admin screens generated from database tables.

There is still one API. Admin operations live under `/api/v1/admin/*` in the FastAPI monolith ([ADR 0002](0002-fastapi-modular-monolith.md)), and the API enforces every role check. The admin app's role gate only decides what to show.

The studio keeps no admin data views. Its `/admin` entry is a link to the portal for staff accounts.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| `/admin` route group inside the studio | One deploy couples learner and staff releases. Admin editors, diff views, and graph tooling end up in the learner build. A shared origin makes a stricter content security policy and shorter staff sessions harder to apply only to staff. |
| Separate admin app on MUI | A second styling system with its own theme, dark mode, focus styles, and component idioms. Nothing could be shared with the studio, and accessibility would be checked against two libraries. MUI X's data grid saves time only for spreadsheet-heavy tools, which this portal is not. |
| Refine or react-admin | Another framework to learn and upgrade. TanStack Query and TanStack Table already cover lists, filters, paging, and mutations. |
| Retool, Appsmith, or a generated database admin | Instructors are product users who author and review content. These tools connect to data directly and bypass the API's role checks, approval workflow, and audit log. |

## Trade-off analysis

Two Next.js projects cost a second Vercel project, a second CI job, and a second set of environment variables. In exchange, a broken admin release cannot take down learners, and the portal can ship a review-queue change on a Tuesday without touching the studio.

One design system means a component written for one app can move to the other unchanged. The price is building table chrome on TanStack Table (column sizing, server sorting, selection, virtual rows) once, as a shared `DataTable`, instead of getting it from MUI X.

Until the apps share packages, the Tailwind tokens and primitives are copied. Copies drift. The rule below limits that.

## Consequences

- `admin/` has its own `package.json`, lockfile, and CI job (typecheck and build).
- Theme tokens in `admin/tailwind.config.js` match `frontend/tailwind.config.js`. A token change lands in both files in the same change.
- The lesson preview in the admin app must render exactly as the studio does. Before the "preview as learner" screen ships, move the renderer (`frontend/components/markdown-view.tsx` and the `.prose-mentor` styles) and the shared primitives into workspace packages:

  ```text
  packages/ui/              Tailwind preset, tokens, primitives (button, dialog, badge, table)
  packages/content-render/  Markdown, KaTeX, and Mermaid renderer
  packages/api-client/      Types generated from docs/openapi.yaml
  ```

- `CORS_ORIGINS` lists both the studio and the admin origin.
- Staff sessions require MFA and use a shorter lifetime than learner sessions ([ADR 0005](0005-clerk-authentication.md)).
- The admin app sends `X-Robots-Tag: noindex` and its own content security policy.
- Adding a UI dependency outside the two tables above requires an amendment to this record.

## Future considerations

- Stripe return URLs are validated against `CORS_ORIGINS`. Once the admin origin is in that list, checkout would accept an admin return URL. Validate return URLs against a studio-only list.
- If the portal later serves institution instructors with their own branding (B2B), it can take its own theme on top of the shared preset rather than a different library.
- Vercel Firewall IP allow-listing for `admin.<domain>` is optional. Turn it on if staff work from fixed networks.

## Amendment — 2026-10-13

The apps moved to Next.js 16.4 to clear SEC-16. Next 16 renames `middleware.ts` to `proxy.ts`; both apps' Clerk protection and per-request CSP nonce now live there. Request APIs (`headers()`, route `params`) were already awaited, so no page changed.
