# Security

This page summarises the controls in the build. [Security-Compliance.md](Security-Compliance.md) is the normative specification; its §0 lists every open finding.

## Access

Clerk verifies the person: an RS256 token from JWKS, with issuer, expiry, not-before, and `azp` checked, and `aud` too when `CLERK_AUDIENCE` is set. PostgreSQL stores the role, and a token never sets it. A new identity is a student. Roles change only through `PATCH /api/v1/admin/users/{id}` (admin only; nobody may change their own role; the last admin cannot be demoted) or the bootstrap command `python -m app.cli grant-admin <clerk_id> --reason …`. Both write an audit row.

Every `/api/v1/admin/*` route requires at least the instructor role before any body is read. The services then apply finer rules: user management, configuration, providers, and the audit log need `admin`. Staff requests need a second factor (Clerk's `fva` claim) when `REQUIRE_STAFF_MFA` is on. It is on by default in production and cannot be turned off there. Suspended accounts get 403.

Dev auth (`X-Dev-User-Id`) exists only when `APP_ENV` is `development` or `test`. The API refuses to start in production with it on, and both frontends refuse to build for production with `NEXT_PUBLIC_DEV_AUTH=true`.

Leaderboards list learners only. Staff, suspended accounts, and anyone who opted out are left off. Each entry shows the learner's chosen handle or a stable pseudonym (`Learner-3f9a1c`), never a name or email.

Documents, conversations, quizzes, cards, and submissions are loaded with the current user id in the query. `tests/integration/test_security.py` checks that another learner gets 404 for each one.

## Input and errors

Pydantic limits lengths on every body. Prompt text is screened. A message that is only an injection attempt is rejected. A lesson question that mentions injection in passing is flagged and still allowed, because students ask about the topic.

Untrusted document text is fenced before it is placed beside instructions. The security prompt in `backend/app/prompts/security.md` is composed into model calls.

Every error is RFC 9457 `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`, and `trace_id`. Validation errors add `errors[]` with field paths. Unexpected exceptions return a generic 500 and are logged with the request id.

## RAG

Learner uploads go to the `learner_docs_v1` collection and curated library chunks to `knowledge_v1`. Searches go through two filter builders, owner plus document or published only, and results are re-checked in PostgreSQL. Archiving or unpublishing an asset deletes its points.

Chunk labels are the only citations a critique may use. If the model does not cite a supplied label, critique, gaps, and future work are dropped. Extractive mode never invents them. Hash embeddings are used only without Qdrant; with Qdrant configured, a missing or failing embedding provider is an error, not a silent fallback.

## Code

The lab is the largest open risk (SEC-01). The static filter rejects private and introspection attributes, module-reaching names, format-string traversal, and imports outside an allowlist. The child then runs `python -I` with a cleared environment, resource limits, a 3 s timeout, and truncated output. That is not isolation. The lab is **off by default in production** and the API refuses to start there with `LAB_ENABLED=true` until learner code runs in a separate, secret-free, network-less runner. Chat does not execute code.

## Edges

- **Webhooks.** Stripe and Clerk signatures are verified (5-minute tolerance). Each event id is stored once in `webhook_events`; replays are acknowledged and ignored. A Stripe event older than the last applied one is ignored.
- **Billing return URLs.** Scheme, host, and port must match `STUDIO_ORIGINS` exactly.
- **Rate limits.** Per user, after authentication: 60 requests a minute, 20 on AI routes, 10 uploads an hour. A per-address ceiling of 120 a minute applies before authentication. Counters are in Redis, which production requires. 429 responses carry `Retry-After` and `RateLimit-*`. Health, readiness, webhooks, and `OPTIONS` are exempt.
- **Headers.** The API sends `default-src 'none'` CSP, `nosniff`, `DENY` framing, `no-referrer`, `no-store` on `/api/*`, and HSTS in production. The studio and admin send a per-request nonce CSP with `strict-dynamic`, and the admin adds `X-Robots-Tag: noindex`.
- **Information.** Production serves no interactive docs; `/health` returns `{"status":"ok"}` only.

## Privacy

`GET /api/v1/me/export` returns the learner's data as JSON. `DELETE /api/v1/me` and the Clerk `user.deleted` webhook erase the learner. Erasure deletes the Clerk user (self-service only), removes Qdrant points by their stored ids, anonymises the Stripe customer, deletes the user row so learner data cascades, and records a non-personal audit row.

## OWASP

| Risk | Control in this build |
| --- | --- |
| Broken access control | Staff gate on admin routes, role checks in services, user-scoped queries, last-admin and self-change guards, four-eyes publishing |
| Cryptographic failures | Clerk RS256 via JWKS; no homegrown passwords; TLS required to Qdrant in production |
| Injection | Parameterized SQLAlchemy queries; prompt screening; fenced documents; markdown URL allowlist |
| Insecure design | No answer keys in quiz payloads; no invented paper critiques; XP idempotent by source |
| Security misconfiguration | Production validator; security headers; docs off in production; powered-by header off |
| Vulnerable components | `pip-audit`, `npm audit`, `bandit`, and gitleaks in CI; no Python lockfile yet (SEC-17) |
| Auth failures | JWT verification with `azp`; staff MFA; dev auth cannot ship in production |
| Integrity | Signed, idempotent, ordered webhooks |
| Logging | JSON logs with request and trace ids; OTLP export when configured |
| SSRF | The API does not fetch arbitrary URLs from learner input |
