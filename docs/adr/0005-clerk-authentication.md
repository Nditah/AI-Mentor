# ADR 0005 — Clerk for authentication

- Status: Accepted (amended 2026-10-13)
- Date: 2026-10-13

## Context

Learners sign up, log in, and use OAuth. The product has three roles: student, instructor, and admin. The API must know who is calling before it returns a dashboard, a document, or a grade. The team should not operate a password database.

## Problem

Choose an identity provider and decide where the role lives so that a login token cannot accidentally demote an admin.

## Decision

Clerk is the identity provider. It issues RS256 JWTs. The API verifies them with Clerk’s JWKS and `CLERK_ISSUER`.

The role of record is `users.role` in Postgres. The API copies a role from token metadata only when that claim is present. A token with no role claim does not overwrite the stored role. New users are students.

`POST /api/v1/webhooks/clerk` verifies the Svix signature and upserts the user. Deleting a Clerk user is not implemented.

Development and test accept `X-Dev-User-Id` matching `^[A-Za-z0-9_-]{1,64}$`. The header selects a user and cannot set a role. `APP_ENV=production` refuses to start when dev auth is on, or when the JWKS URL or issuer is missing.

Seeded staff ids `demo-student`, `demo-instructor`, and `demo-admin` exist for local smoke tests. They are not a production login.

Stripe is separate. Checkout stays HTTP 503 until Stripe keys exist. Subscription status is updated from the Stripe webhook.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| A second password store in Postgres | Two sources of “who is this person,” plus reset email, breach response, and OAuth we would have to build. |
| Auth.js inside Next.js only | The API would trust a cookie it does not verify, or the studio would have to mint a second token. Clerk JWTs are verified at the API. |
| Azure Entra ID as the learner IdP | Fits staff SSO later. It is a heavy account model for a public learner sign-up. |
| Roles only in Clerk metadata | An empty metadata payload on a later token would demote an admin. Postgres is the authority. |

## Trade-off analysis

Clerk removes password storage and provides OAuth. The cost is a vendor on the login path: if Clerk is down, production login is down, because there is no password fallback.

Verifying JWT at the API means the studio cannot grant itself a role by hiding a header. The development header is powerful and is fenced by the production settings validator.

Role changes for existing users go through `PATCH /api/v1/admin/users/{id}`, which requires an admin. The last admin cannot be demoted.

Public routes stay public: health, the path list, the knowledge graph, lab project briefs, and the leaderboard. The leaderboard returns display name, XP, level, and streak. It does not return email.

## Consequences

- Every learner-owned row is loaded with the current user id.
- The studio must send `Authorization: Bearer` in production and must stop sending `X-Dev-User-Id` when `NEXT_PUBLIC_DEV_AUTH` is unset.
- Webhook secrets live in Key Vault, not in the image.
- A Clerk user deletion does not yet remove Postgres rows. That is an open item before a public launch.

## Future considerations

- Implement the user-deleted webhook as a defined retention action, with a decision on whether progress is erased or detached.
- Add staff SSO through Clerk enterprise or a separate Entra tenant if operators need it. Learner login stays on Clerk.
- Protect studio routes with `clerkMiddleware` before the first production cut.

## Amendment — 2026-10-13 hardening

This replaces the parts of the decision above that no longer hold.

- **Roles are never read from a token or webhook.** The "copy a role from token metadata when present" rule is withdrawn: any claim an end user can influence must not grant privilege. The role of record is `users.role`, changed only by an admin in the portal (audited with previous role, new role, and reason) or by `python -m app.cli grant-admin` for the first admin (audited `via: cli`). An admin cannot change their own role, and the last admin cannot be demoted (409).
- **Token checks:** RS256 against the JWKS (5 s timeout, one-hour key cache), `iss`, `exp`, `nbf`, `iat`, and `azp` in `CLERK_AUTHORIZED_PARTIES`, plus `aud` when `CLERK_AUDIENCE` is set, with `JWT_LEEWAY_SECONDS` skew. An unreachable JWKS is 503; a bad token is 401 with `WWW-Authenticate: Bearer`.
- **Staff MFA:** in production, instructor and admin calls require a verified second factor (`fva`), otherwise 403. Suspended accounts are 403.
- **Identity sync:** first sight creates a `student`. Afterwards only email and name are refreshed, and only when they changed.
- **Clerk webhooks:** `user.created` and `user.updated` refresh email and name. `user.deleted` erases the learner (vectors, Stripe customer anonymised, rows deleted, audited by subject hash). Each `svix-id` is applied once. The open item in the consequences below is closed.
- **Erasure from the product:** `DELETE /api/v1/me` erases the account, including the Clerk user via `CLERK_SECRET_KEY`. `GET /api/v1/me/export` returns the learner's data.
- **Frontends:** both apps mount `ClerkProvider` and protect routes with `clerkMiddleware` when a publishable key is set, send `Authorization: Bearer`, and refuse to build for production with dev auth on or without a key. The future consideration about `clerkMiddleware` is done.
- **Demo accounts** are seeded only in development and test.
- The leaderboard shows a handle or a stable pseudonym, never the display name (SRS GAM-005).
