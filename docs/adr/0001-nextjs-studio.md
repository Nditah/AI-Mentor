# ADR 0001 — Next.js for the studio

- Status: Accepted (amended 2026-10-13), amended by [ADR 0012](0012-separate-admin-app.md)
- Date: 2026-10-13

> Amendment (ADR 0012): admin screens moved out of the studio into a separate Next.js app in `admin/` on its own subdomain. Both apps keep the stack chosen here. Read "admin" below as historical.

## Context

AI Mentor needs a public marketing site and a signed-in studio: dashboard, tutor, quiz, paths, concept map, flashcards, coding lab, research, and admin. The studio talks to a separate FastAPI mentor. Learners expect a responsive, dark-mode interface with markdown, mathematics, and diagrams in tutor replies.

## Problem

Choose a web framework that can ship a server-rendered landing page and a client-side studio without splitting the product into two frontends.

## Decision

Build the studio with Next.js 15 App Router, React 19, and TypeScript. Tailwind CSS supplies the visual system. TanStack Query owns server state. Zustand holds only local UI state: notes, the lab draft, and the development session id. Tutor and lesson content render through `react-markdown`, KaTeX, and Mermaid with `securityLevel: "strict"`.

The production studio deploys to Vercel. A standalone `frontend/Dockerfile` exists for a self-hosted build and is not the primary path.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Vite SPA with React Router | The landing page and studio would share no server rendering, and preview deploys would be a separate project. |
| Remix | A strong fit for forms, and a second framework to staff beside an already chosen App Router. |
| Server-rendered templates inside FastAPI | The tutor, lab editor, and theme toggle are interactive. Folding them into Jinja would recreate a frontend inside the API. |
| React Native or a separate mobile client | Out of scope until the web studio is the product learners actually finish. |

## Trade-off analysis

App Router gives one project for the marketing page and the studio, file-based routes, and preview deployments per pull request. The cost is a build pipeline that must stay in lockstep with React 19, and a client bundle that includes markdown and Mermaid. Those libraries stay on the tutor, path, and graph routes.

TanStack Query refetches the dashboard after a lesson, quiz, review, or lab run. Zustand does not cache API payloads, so a role change in the session switcher cannot leave a stale dashboard in a second store.

Clerk’s React SDK is the intended production session. The current build runs without a publishable key and uses a development header. That split is deliberate and is closed before a public launch. See ADR 0005.

## Consequences

- Studio routes live under `frontend/app`. The landing page is a server component. Studio pages that call the API are client components.
- `NEXT_PUBLIC_*` values are public. API secrets never enter this bundle.
- CI runs `tsc` and `next build` on every push.
- Accessibility targets WCAG AA: skip link, labelled controls, and button colours chosen for contrast. Accent green is used for the XP meter, not for small text.

## Future considerations

- Mount `ClerkProvider` and `clerkMiddleware` on studio routes, then remove the development session switcher from public builds.
- Stream tutor tokens only after the socratic policy still owns the first turns. See ADR 0010.
- Add a shared rate-limit and request-id header display when Front Door sits in front of the API. See ADR 0006.

## Amendment — 2026-10-13

The apps moved to Next.js 16.4 to clear SEC-16. Next 16 renames `middleware.ts` to `proxy.ts`; both apps' Clerk protection and per-request CSP nonce now live there. Request APIs (`headers()`, route `params`) were already awaited, so no page changed.
