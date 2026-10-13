# AI Mentor — API Specification v2 (multi-application platform)

| Field | Value |
| --- | --- |
| Document | API Specification v2 |
| Version | 2.0 |
| Date | 13 October 2026 |
| Status | Approved direction. Target contract; v2 operations are not routed yet |
| Owner | Enterprise Architecture with the Backend lead |
| Related | [README.md](README.md), [06-system-architecture.md](06-system-architecture.md), [07-database-design.md](07-database-design.md), [09-security-model.md](09-security-model.md), [10-rbac-matrix.md](10-rbac-matrix.md), [../API.md](../API.md), [../openapi.yaml](../openapi.yaml), [../SystemArchitecture.md](../SystemArchitecture.md) section 12, [ADR 0013](../adr/0013-five-applications-shared-platform.md), [ADR 0015](../adr/0015-organisation-tenancy.md), [ADR 0016](../adr/0016-scoped-rbac-abac.md), ADR 0018, ADR 0026 |

## Change record

| Area | What changed | Why | Impacted systems | Implementation implications |
| --- | --- | --- | --- | --- |
| API roots | Flat learner and `/admin` routes become six roots: `/me`, `/learn`, `/orgs/{org_id}`, `/content`, `/platform`, and standards endpoints | Each root has one tenant rule and one set of app audiences (ADR 0013) | All routers, all five apps, `packages/api-client` | New routers per context; v1 paths kept as deprecated aliases until the end of R2 |
| Tenant scoping | Every tenant-scoped call carries the organisation in the path or `X-Org-Id` | One active tenant per request (ADR 0015) | API, apps, caches | Tenant context dependency; mismatch is 400 |
| Authorisation | Every operation names a permission and its attribute conditions | Scoped RBAC with ABAC (ADR 0016) | API, RBAC matrix | `require(...)` on every route; route-coverage test |
| Conventions | Idempotency keys, cursor pagination, ETags, async jobs, problem types, deprecation headers are mandatory for v2 operations | Bulk classroom work, concurrent content editing, retries from mobile clients | API kernel, client package | Shared kernel helpers; contract tests |
| Errors | `about:blank` problems gain specific `urn:ai-mentor:problem:<kind>` types; catalogue fixed | Clients need stable machine-readable failures | API, apps | Problem handler mapping; `openapi.yaml` description corrected |
| Integrations | LTI 1.3, SCIM 2.0, OneRoster, xAPI, and outbound webhooks are specified | Institutional interoperability (ADR 0026) | `integration` context | Standards endpoints outside `/api/v1` |
| Rate limits | Per-user limits gain per-tenant budgets and AI quotas | Noisy-neighbour control at 2,000 organisations | Redis limiter, `ai_gateway` | New 429 variants with `limit_scope` |

## Relationship to v1 documents

| v1 document | Status |
| --- | --- |
| [openapi.yaml](../openapi.yaml) | **Remains the contract for live routes.** Operations in this document are target operations. Each is added to `openapi.yaml` with `x-implementation: contract` when its design is accepted, and switched to `live` when it ships. `packages/api-client` is generated from that file only |
| [API.md](../API.md) | Describes the live routes. Changes when code changes |
| [SystemArchitecture.md](../SystemArchitecture.md) section 12 | Gateway layers (12.1), Front Door routes (12.2), rate classes (12.3), and middleware order (12.4) stay normative, as amended by [06](06-system-architecture.md) section 7. The conventions table (12.5) is replaced by section 2 below. The target v1 catalogue (12.6) is replaced by section 5 |

Two v1 statements disagree with the running code. The code wins and the v1 text is a defect to fix in the first pull request that adds v2 operations:

- The `openapi.yaml` description says domain errors are `{ "detail": "..." }` and rate limits are keyed by client IP. The code returns RFC 9457 problem details (`app/core/problems.py`) with `trace_id`, and rate limits are per user after authentication with a per-address ceiling (`API.md`).
- v1 SAD 12.5 lists `request_id` in the problem body. The code uses `trace_id` in the body and `X-Request-Id` as a header. This document keeps the code's shape.

## Contents

1. [Status and contract](#1-status-and-contract)
2. [Principles and conventions](#2-principles-and-conventions)
3. [Authentication](#3-authentication)
4. [Authorisation annotations](#4-authorisation-annotations)
5. [Endpoint catalogue](#5-endpoint-catalogue)
6. [Worked examples](#6-worked-examples)
7. [Error catalogue](#7-error-catalogue)
8. [Event-to-webhook mapping](#8-event-to-webhook-mapping)
9. [SDK and client generation](#9-sdk-and-client-generation)
10. [Mobile and partner API considerations](#10-mobile-and-partner-api-considerations)
11. [Mapping from v1 routes](#11-mapping-from-v1-routes)
12. [Appendix: names introduced by this document](#12-appendix-names-introduced-by-this-document)

---

## 1. Status and contract

| Marker | Meaning |
| --- | --- |
| `live` | Routed by the current FastAPI app; schemas match the handlers ([openapi.yaml](../openapi.yaml)) |
| `contract` | Agreed shape; returns 404 until the handler ships. Every operation in section 5 is `contract` today unless its Notes say "live (v1 path …)" |
| R1–R5 | Product release in which the operation is expected to ship ([README releases](README.md#releases)) |

Base URL: `https://api.<domain>`. Application operations are under `/api/v1`. Standards endpoints (`/lti`, `/scim/v2`, `/webhooks`) are on the root because external specifications fix their shape.

---

## 2. Principles and conventions

### 2.1 One API, resource-oriented

- One API, `/api/v1`, for all five apps, mobile clients, and partners. There is no app-specific backend.
- Paths are kebab-case plural nouns (`/cohort-plans`, `/ai-proposals`). Identifiers are UUIDv7 strings; slugs are accepted only where the v1 API already uses them (concepts, public catalogue).
- State transitions that are not a field update use `POST` to a named action sub-resource: `/submit`, `/accept`, `/override`, `/publish`, `/schedule`, `/transitions`. Each action is idempotent with an `Idempotency-Key`.
- Responses are JSON (`application/json`), errors are `application/problem+json`, streams are `text/event-stream`.
- Fields are `snake_case`. Timestamps are RFC 3339 UTC (`2026-10-13T14:50:00Z`). Dates without time are `YYYY-MM-DD` in the organisation's time zone, which every date-bearing resource names (`time_zone`). Money is `{ "amount_minor": 120000, "currency": "GBP" }`.

### 2.2 Tenant scoping

| Root | Tenant rule |
| --- | --- |
| `/api/v1/orgs/{org_id}/...` | Tenant is the path parameter. If `X-Org-Id` is also sent and differs, 400 `tenant-mismatch` |
| `/api/v1/learn/...` | Tenant is `X-Org-Id`; absent means the person's home tenant (ADR 0015) |
| `/api/v1/me/...` | Person-level. `X-Org-Id` is honoured by tenant-specific resources (`/me/branding`, `/me/notifications` filter) |
| `/api/v1/content/...` | Tenant is the owner of the workspace in the path |
| `/api/v1/platform/...` | Platform context. Reads of tenant data require `X-Access-Reason` (free text, 10–500 characters, recorded in `audit.data_access_log`) |

The API validates the tenant against an `active` membership (or a platform role for `/platform`). Every response that is tenant-scoped carries `X-Org-Id` back so clients and caches can key on it.

### 2.3 App audience restrictions

The API maps the token's `azp` to an app code (`APP_AUDIENCES`) and rejects a root the app may not call with 403 `wrong-app-audience` (ADR 0013).

| Root | Accepted apps |
| --- | --- |
| `/me` | All five apps and registered mobile clients |
| `/learn` | Learner App, Learner mobile |
| `/orgs/{org_id}` | Instructor App, Institution App, Instructor mobile (R5) |
| `/content` | Content Studio |
| `/platform` | Admin App; writes need MFA within 15 minutes |
| Standards endpoints | No app token; their own credentials (section 3.3) |

Individual operations may narrow this further (for example `/orgs/{org_id}/sso-connections` accepts only the Institution App). Notes in section 5 say so.

### 2.4 Idempotency

- `Idempotency-Key` (1–128 characters, a UUID is recommended) is **required** on every `POST` that creates a resource, awards something (XP, badges, seats, grades), starts a job, or sends a message. It is optional on other `POST`s.
- The server stores (principal, tenant, method, path, key) with a hash of the body and the response for 24 hours.
- A repeat with the same body returns the stored response with `Idempotent-Replayed: true`. A repeat with a different body is 422 `idempotency-key-reused`. A repeat while the first is still running is 409 `idempotency-in-progress` with `Retry-After: 1`.
- Database uniqueness (for example `game.xp_ledger` source keys) remains the final guarantee for awards (v1 principle P9).

### 2.5 Pagination, filtering, and sorting

| Concern | Convention |
| --- | --- |
| Pagination | Cursor based. `?limit=` (default 25, maximum 100) and `?cursor=` (opaque). Response `{ "items": [...], "next_cursor": "…" or null }`. No total by default; `?include=total` adds `total` where it is cheap |
| Filtering | Plain query parameters named after fields: `?status=published&cohort_id=…`. Multiple values are comma-separated (`?status=draft,in_review`). Ranges use `_from` and `_to` suffixes (`?due_from=2026-10-01`) |
| Text search | `?q=` on list endpoints that support it; the unified search is `/learn/search` and per-root search endpoints |
| Sorting | `?sort=` with comma-separated fields, `-` for descending (`?sort=-due_at,name`). Each list documents its sortable fields; others are 422 |
| Sparse fields | `?fields=` is not supported in v2; views are shaped by the endpoint |
| Expansion | `?include=` names related objects to embed where documented (`?include=staff,plan`) |

### 2.6 Errors: RFC 9457 problem details

Every error is `application/problem+json`:

```json
{
  "type": "urn:ai-mentor:problem:forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "You are not on the teaching staff of this cohort.",
  "instance": "/api/v1/orgs/0192f1c4-7a2e-7c11-9a55-2f0d3c1b8e01/cohorts/0192f1c4-8b10-7d02-8c3e-5a9e7f6d1c22/plans",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "permission": "classroom.cohort_plan:schedule",
  "reason_code": "not_cohort_staff"
}
```

- `type` is stable and machine-readable; section 7 lists them. `title` is the HTTP phrase. `detail` is a sentence localised by `Accept-Language`.
- Extension members are allowed per type: `errors[]` (`{path, message}`) for validation, `permission` and `reason_code` for authorisation, `limit_scope` for rate limits, `max_age_seconds` for MFA step-up, `current_etag` for precondition failures.
- A 404 is returned instead of 403 when revealing existence would leak data (another tenant's resource, a learner outside the caller's scope).

**Migration from v1.** The live API already returns RFC 9457 bodies with `type: about:blank` for most errors and three typed kinds (`validation`, `rate-limited`, `not-ready`). Clients that read only `detail` keep working because `detail` stays. Steps: (R1) correct the `openapi.yaml` description and add a shared `Problem` schema to every operation; (R1) map existing `ClientError` subclasses to the types in section 7; (R2) v2 operations use only catalogue types; `about:blank` remains only for unexpected 500s.

### 2.7 Versioning and deprecation

- The URI version stays `/api/v1`. Additive changes (new fields, new optional parameters, new operations, new enum values on response fields documented as open) are not breaking. Clients must ignore unknown fields.
- A breaking change ships as a new resource or a new field, never as a changed meaning. A whole-API break would be `/api/v2`, with v1 kept for 6 months for first-party apps and 12 months for partner clients.
- Deprecated operations send `Deprecation: @<unix-time>` (RFC 9745), `Sunset: <HTTP-date>` (RFC 8594), and `Link: <replacement>; rel="successor-version"`. Deprecations are announced in the changelog and to webhook and partner contacts at least 90 days before sunset.
- Event payloads version independently (`.v<n>` in the CloudEvents type).

### 2.8 Optimistic concurrency with ETags

- Editable content and configuration resources (lessons, modules, courses, paths, items, rubrics, assessments, overlays, plans, branding, policies, SSO connections) return a strong `ETag` derived from the row version (`"r17"`).
- `PATCH`, `PUT`, and state transitions on those resources **require** `If-Match`. Missing is 428 `precondition-required`; stale is 412 `precondition-failed` with `current_etag`.
- `GET` with `If-None-Match` returns 304 when unchanged; clients and BFFs use this for catalogue and lesson reads.

### 2.9 Bulk operations as asynchronous jobs

Any operation that may touch more than 500 rows, call a model for many items, or produce a file returns `202 Accepted`:

```http
HTTP/1.1 202 Accepted
Location: /api/v1/orgs/{org_id}/jobs/0192f1c5-0e41-7a9b-b2d4-91f0c3e2aa10
Retry-After: 2
```

```json
{
  "id": "0192f1c5-0e41-7a9b-b2d4-91f0c3e2aa10",
  "kind": "cohort_member_import",
  "status": "queued",
  "progress": { "processed": 0, "total": null },
  "created_at": "2026-10-13T14:50:00Z",
  "links": { "self": "/api/v1/orgs/{org_id}/jobs/0192f1c5-0e41-7a9b-b2d4-91f0c3e2aa10" }
}
```

Job `status` is `queued`, `running`, `succeeded`, `partially_succeeded`, `failed`, or `cancelled`. A finished job has `result` (counts and resource links) and, when rows failed, `errors_url` (a signed CSV link, valid 24 h). Jobs live under the root that created them: `/me/jobs`, `/orgs/{org_id}/jobs`, `/content/jobs`, `/platform/jobs`. `POST …/jobs/{job_id}/cancel` stops a queued or running job where the kind allows it. Completion also emits a notification to the requester.

### 2.10 Outbound webhooks

| Concern | Rule |
| --- | --- |
| Registration | Organisation admins register endpoints at `/orgs/{org_id}/webhook-endpoints` with an HTTPS URL and a list of event types (section 8) |
| Payload | CloudEvents 1.0 structured JSON, same `id` and `type` as the domain event, `data` limited to the fields in section 8 |
| Signature | Standard Webhooks: headers `webhook-id` (event id), `webhook-timestamp` (Unix seconds), `webhook-signature` (`v1,<base64 HMAC-SHA256 of id.timestamp.body>`). Secrets are 32 random bytes, shown once, rotatable with a 24 h overlap during which both signatures are sent |
| Delivery | At least once. Receivers de-duplicate on `webhook-id` and reject timestamps older than 5 minutes |
| Retries | On a non-2xx response or a 10 s timeout: retries at 5 s, 5 min, 30 min, 2 h, 5 h, 10 h, then every 10 h up to 5 days. After 5 days of continuous failure the endpoint is disabled and `integration.webhook.disabled` notifies the organisation's admins |
| Ordering | Not guaranteed. Payloads carry `occurred_at` and the aggregate version where relevant |
| Logs | `GET /orgs/{org_id}/webhook-endpoints/{id}/deliveries` lists attempts for 30 days; `POST …/deliveries/{delivery_id}/redeliver` resends one |

### 2.11 Rate limits

Two buckets apply to every authenticated call: per user (v1 SAD 12.3 classes) and per tenant (06 section 8.5). AI routes also check the tenant AI quota.

| Class | Per user (Free / Pro / Research / organisation seat) | Per tenant |
| --- | --- | --- |
| `api` | 120 / 300 / 300 / 300 per minute | 20 per seat per minute, minimum 600, maximum 60,000 |
| `ai` | 20 / 60 / 60 / 60 per minute; daily token budget | Monthly AI quota from the licence |
| `exec` | 10 / 30 / 30 / 30 per minute | 5 per seat per minute |
| `upload` | 0 / 5 / 50 / 20 per day | Plan-defined |
| `bulk` | 10 jobs per hour | 2 running jobs per kind |
| `platform` | 300 per minute (Admin App) | Not applicable |
| `standards` | Not applicable | SCIM and LTI: 600 per minute per client or deployment |
| `anon` | 30 per minute per address | Not applicable |

Responses carry `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`, and on 429 `Retry-After`. The 429 problem says which bucket tripped in `limit_scope` (`user`, `tenant`, `address`, `ai_quota`).

### 2.12 Localisation

- `Accept-Language` selects the response locale among `en`, `fr`, `es`; the response sends `Content-Language`. Fallback is the requested locale, then the organisation default, then `en`.
- Localisable resources include `locale` (the locale of the returned text), `source_locale`, and `available_locales`. Content Studio resources expose `translations[]` with `locale` and `translation_status` (`missing`, `machine_draft`, `in_review`, `approved`).
- A graded item is served in a locale only when its translation is `approved`; otherwise the source locale is returned and `locale` says so.
- `detail` in problems and notification text are localised; `type`, enum values, and identifiers never are.

### 2.13 Streaming

Tutor turns and live notifications use Server-Sent Events over `POST` (tutor) or `GET` (notifications) with a heartbeat comment every 15 s. Clients use `fetch` with a stream reader so they can send `Authorization` (v1 SAD 6.3).

---

## 3. Authentication

### 3.1 Clerk session tokens (apps)

| Check | Rule |
| --- | --- |
| Token | `Authorization: Bearer <Clerk session JWT>`, RS256 from the Clerk JWKS, `iss` = `CLERK_ISSUER`, `exp` and `nbf` with 5 s leeway, `sub` present |
| Authorised party | `azp` must be in `CLERK_AUTHORIZED_PARTIES` and map to an app code in `APP_AUDIENCES`; otherwise 401 |
| Roles | Never read from the token. Assignments come from `authz.role_assignments` (SEC-02, ADR 0016) |
| MFA freshness | Clerk's `fva` claim (`[first_factor_age_minutes, second_factor_age_minutes]`). Operations marked **MFA ≤ n** in section 5 require a second factor within n minutes; otherwise 403 `mfa-step-up-required` with `max_age_seconds`. The app runs Clerk reverification and retries |
| Suspended accounts or memberships | 403 `account-suspended` or `not-a-member` |
| Development | `X-Dev-User-Id` as in [API.md](../API.md); never in production |

### 3.2 Sensitive operations

MFA within 15 minutes: every `/platform` write; `tenancy.sso_connection:configure`; domain verification; granting or revoking `org_owner`, `org_admin`, `org_compliance_officer`, `org_billing_manager`; SCIM token and webhook secret creation; compliance erasure requests; audit exports; content publishing. MFA within 60 minutes when the organisation enables it: grade release and grade overrides.

### 3.3 Service credentials

| Caller | Credential | Tenant binding |
| --- | --- | --- |
| SCIM client | Bearer token (`scim_` prefix, 40 random bytes) created at `/orgs/{org_id}/scim-clients`, stored hashed (SHA-256), shown once, rotatable | The SCIM client's organisation |
| LTI platform (inbound launch) | OIDC third-party login, then an `id_token` JWT signed by the platform, verified against the registered JWKS URL; `nonce` and `state` checked | Resolved from (`iss`, `deployment_id`) |
| AI Mentor to LTI platform (AGS, NRPS) | OAuth 2.0 client credentials with `private_key_jwt`; AI Mentor's keys published at `/lti/jwks` | Per LTI registration |
| OneRoster provider | OAuth 2.0 client credentials stored in Key Vault per sync configuration | The sync's organisation |
| Stripe, Clerk webhooks | Provider signatures (v1, unchanged) | Resolved from the event |
| Partner clients (R5) | OAuth 2.0 client credentials at `/api/v1/integrations/oauth/token`; access tokens bound to one organisation and a permission subset | The partner grant's organisation |
| Workers and jobs | Managed identity to Azure services; in the API they act as `system` principals with one function each | From the event or job |

---

## 4. Authorisation annotations

Every operation in section 5 lists a **permission** in `<context>.<resource>:<action>` form and, where they apply, **conditions** evaluated by the policy engine (ADR 0016). The scope check (the role assignment's scope contains the target) is implied for every permission and is not repeated.

| Condition | Meaning |
| --- | --- |
| `self` | The subject is the resource owner (own profile, own submission) |
| `same_tenant` | Resource `tenant_id` equals the active tenant (always applied; listed only for emphasis) |
| `is_cohort_staff` | Subject is in `classroom.cohort_staff` for the resource's cohort |
| `is_ta_delegated(action)` | Subject is a TA with the delegation for this action on the cohort |
| `not_author` | Subject did not author the content version (two-person rule) |
| `mfa_within(n)` | Second factor within n minutes |
| `app_audience(x)` | Token `azp` maps to app x |
| `integrity_mode_off` | No integrity-enabled assessment window is open for the learner |
| `window_open` | Assessment window is open (and accommodations applied) |
| `released` | Grade or feedback has been released |
| `consent_granted(x)` | Learner granted consent x to the organisation (ADR 0021) |
| `seat_assigned` | The learner's membership holds a seat on a licence that includes the feature |
| `entitled(x)` | Plan or licence includes entitlement x |
| `org_policy(x)` | Organisation policy flag x is on |
| `reason_recorded` | `X-Access-Reason` present (platform reads of tenant data) |
| `ticket_ref` | `X-Support-Ticket` present (support agent reads) |
| `public` | No authentication required |

---

## 5. Endpoint catalogue

Paths are relative to `/api/v1` unless they start with `/lti`, `/scim/v2`, or `/webhooks`. "Notes" gives the release and any audience narrowing, MFA, job, or concurrency behaviour.

### 5.1 `/me` — the signed-in person

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET | `/me` | Profile, account type, home tenant, locale, time zone | `self` | R1; live (v1 path `/me`), gains `account_type`, `home_tenant_id` |
| PATCH | `/me` | Update handle, locale, time zone, country, leaderboard opt-out | `self` | R1; live |
| GET | `/me/apps` | App launcher: apps and organisations per app | `self` | R1 (ADR 0013) |
| GET | `/me/memberships` | Organisations the person belongs to, status, consent | `self` | R1 |
| POST | `/me/memberships` | Join an organisation with an enrolment code or invitation token, with consent choices | `self`; personal accounts only, with a valid invitation or enrolment code | R3; Idempotency-Key |
| PATCH | `/me/memberships/{membership_id}` | Change consent given to the organisation | `self`, `consent_granted` changes only | R3 |
| DELETE | `/me/memberships/{membership_id}` | Leave an organisation | `self`; personal accounts only | R3; academic record stays with the organisation |
| GET, PATCH | `/me/preferences` | Learning preferences, mentor technique, accessibility | `self` | R1 |
| GET, PATCH | `/me/dimensions` | Dimension settings with effective values and locks per active tenant | `self` | R2; locked dimensions return 409 `dimension-locked` on change |
| GET | `/me/personas` | Persona catalogue available in the active tenant | `self` | R2 |
| PUT | `/me/persona` | Choose a mentor persona | `self` | R2 |
| GET | `/me/notifications` | In-app notifications (cursor) | `self` | R1 |
| PATCH | `/me/notifications/{notification_id}` | Mark read or archived | `self` | R1 |
| GET | `/me/notifications/stream` | SSE stream of new notifications | `self` | R2 |
| GET, PATCH | `/me/notification-preferences` | Per type and channel | `self` | R2; mandatory types per organisation policy cannot be turned off |
| POST | `/me/devices` | Register a push token for mobile | `self` | R4 |
| GET | `/me/branding` | Branding for the active tenant (`X-Org-Id`) | `self`, member | R1 (consumer default), R3 |
| POST | `/me/events` | Batch of product analytics events from `analytics-client` | `self` | R1; up to 100 events, 64 KB |
| GET | `/me/learning-record` | Mastery, XP, badges across tenants the person controls | `self` | R2 |
| GET | `/me/export` | Data export (JSON) | `self` | R1; live; becomes async (`202`) when large |
| DELETE | `/me` | Erase a personal account | `self`, MFA ≤ 15 if enrolled; personal accounts only | R1; live; managed accounts get 403 `managed-account` |
| GET | `/me/jobs/{job_id}` | Status of the person's job | `self` | R1 |

### 5.2 `/learn` — learner experience in the active tenant

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET | `/learn/dashboard` | XP, streak, mastery bands, next items, due work | `learning.progress:read` (`self`) | R2; replaces `/dashboard` |
| GET | `/learn/catalogue` | Courses and paths visible in this tenant | `learning.catalogue:read` | R2; public variant for guests via `public` filter |
| GET | `/learn/catalogue/courses/{course_id}` | Course detail at the visible release | `learning.catalogue:read` | R2 |
| GET | `/learn/catalogue/paths/{path_id}` | Path detail | `learning.catalogue:read` | R2; replaces `/learning-paths/{slug}` |
| GET | `/learn/lessons/{lesson_id}` | Lesson body in the requested locale and style | `learning.lesson:study`, enrolled or public | R2; ETag |
| POST | `/learn/lessons/{lesson_id}/completions` | Mark lesson complete; returns XP awarded | `learning.lesson:study` (`self`) | R2; Idempotency-Key; replaces `/progress/lessons/{slug}/complete` |
| GET | `/learn/enrolments` | The learner's enrolments in this tenant | `learning.progress:read` (`self`) | R2 |
| POST | `/learn/enrolments` | Self-enrol in a course or path | `learning.enrolment:create` (`self`, `entitled(course)`) | R2; Idempotency-Key |
| DELETE | `/learn/enrolments/{enrolment_id}` | Withdraw a self-enrolment | `learning.enrolment:withdraw` (`self`) | R2; cohort enrolments cannot be withdrawn here |
| GET | `/learn/progress` | Progress per release | `learning.progress:read` (`self`) | R2 |
| GET | `/learn/mastery` | Mastery per concept | `learning.progress:read` (`self`) | R2 |
| GET | `/learn/recommendations` | Next-best items with reason codes | `self` | R2 |
| GET | `/learn/cohort-plans` | Plans for the learner's cohorts with dated items | `learning.lesson:study` (cohort member) | R3 |
| GET | `/learn/cohort-plans/{plan_id}` | One plan with overlay applied | `learning.lesson:study` (cohort member) | R3 |
| GET | `/learn/assignments` | Assignments issued to the learner | `assessment.submission:submit` (`self` assigned) | R3 |
| GET | `/learn/assignments/{assignment_id}` | Assignment with items (when `window_open`) | `assessment.submission:submit` (`self` assigned), `window_open` for items | R3 |
| POST | `/learn/assignments/{assignment_id}/submissions` | Start or save a submission | `assessment.submission:submit` (`self`, `window_open`) | R3; Idempotency-Key |
| PATCH | `/learn/submissions/{submission_id}` | Save responses on a draft submission | `assessment.submission:submit` (`self`, `window_open`) | R3; If-Match |
| POST | `/learn/submissions/{submission_id}/submit` | Submit for marking | `assessment.submission:submit` (`self`, `window_open`) | R3; Idempotency-Key; emits `assessment.submission.submitted` |
| GET | `/learn/grades` | Released grades and feedback | `assessment.grade:read` (`self`, `released`) | R3 |
| GET | `/learn/tutor/modes` | Modes available now, with integrity state | `tutor.conversation:use` (`self`) | R2 |
| GET | `/learn/tutor/conversations` | Conversation list | `tutor.conversation:use` (`self`) | R2; replaces `/conversations` |
| POST | `/learn/tutor/conversations` | Start a conversation with mode, persona, optional lesson or concept context | `tutor.conversation:use` (`self`) | R2; Idempotency-Key |
| GET | `/learn/tutor/conversations/{conversation_id}` | Messages | `tutor.conversation:use` (`self`) | R2 |
| POST | `/learn/tutor/conversations/{conversation_id}/messages` | Tutor turn; SSE when `Accept: text/event-stream` | `tutor.conversation:use` (`self`, mode allowed, `integrity_mode_off` for blocked modes) | R2; rate class `ai`; replaces `/chat` and `/chat/stream` |
| POST | `/learn/tutor/messages/{message_id}/feedback` | Thumbs up or down with reason | `tutor.conversation:use` (`self`) | R2 |
| POST | `/learn/tutor/messages/{message_id}/flags` | Report a reply | `tutor.conversation:use` (`self`) | R2; emits `tutor.message.flagged` |
| POST | `/learn/practice/quizzes` | Generate a practice quiz | `learning.practice:use` (`self`, `integrity_mode_off`) | R2; `ai`; replaces `/quiz/generate` |
| POST | `/learn/practice/quizzes/{quiz_id}/attempts` | Grade a practice quiz | `learning.practice:use` (`self`) | R2; Idempotency-Key; replaces `/quiz/{id}/grade` |
| GET | `/learn/practice/flashcards/due` | Due cards | `learning.practice:use` (`self`) | R2 |
| POST | `/learn/practice/flashcards` | Generate cards for a concept | `learning.practice:use` (`self`) | R2; `ai` |
| POST | `/learn/practice/flashcards/{card_id}/reviews` | SM-2 review | `learning.practice:use` (`self`) | R2; Idempotency-Key |
| GET | `/learn/practice/lab/projects` | Lab projects | `learning.practice:use` | R2 |
| POST | `/learn/practice/lab/runs` | Run code in the sandbox | `learning.practice:use` (`self`, `entitled(lab)`) | R2; rate class `exec` |
| POST | `/learn/practice/lab/reviews` | Coding review | `learning.practice:use` (`self`) | R2; `ai` |
| GET | `/learn/challenges/today` | Daily challenge | `learning.practice:use` | R2 |
| POST | `/learn/challenges/{challenge_id}/attempts` | Submit challenge | `learning.practice:use` (`self`) | R2; Idempotency-Key |
| POST | `/learn/research/documents` | Upload a paper | `retrieval.document:upload` (`self`, `entitled(research)`) | R2; rate class `upload`; 202 |
| POST | `/learn/research/analyses` | Analyse an owned document | `retrieval.document:upload` (`self`) | R2; `ai` |
| POST, GET | `/learn/study-plans` | Create and list self-directed plans | `self` | R2 |
| GET | `/learn/gamification/summary` | XP, level, title, streak, season standing | `learning.progress:read` (`self`) | R2 |
| GET | `/learn/gamification/badges` | Earned and available badges | `learning.progress:read` (`self`) | R2 |
| GET | `/learn/gamification/xp-events` | XP ledger (cursor) | `learning.progress:read` (`self`) | R2 |
| GET | `/learn/leaderboards` | Ranked entries for `scope` (`global`, `country`, `organisation`, `cohort`, `friends`, `competition`), `scope_id`, `period`, `metric` | `gamification.leaderboard:read` (scope visible to the learner; `org_policy(leaderboards)` for organisation and cohort) | R2 (global, country, friends), R3 (organisation, cohort, competition); public top 10 stays at v1 `/leaderboard` |
| GET | `/learn/leaderboards/standing` | The learner's rank and percentile per scope | `gamification.leaderboard:read` (`self`) | R2 |
| GET | `/learn/competitions` | Competitions open to the learner | `gamification.leaderboard:read` | R3 |
| POST | `/learn/competitions/{competition_id}/entries` | Join a competition | `learning.practice:use` (`self`, eligible) | R3; Idempotency-Key |
| GET, POST | `/learn/friends` | Friends list and requests | `gamification.visibility:edit` (`self`) | R2 |
| PATCH | `/learn/friends/{friendship_id}` | Accept, decline, block | `gamification.visibility:edit` (`self`) | R2 |
| GET | `/learn/search` | Unified search in the active tenant (`q`, `types`) | `learning.catalogue:read`; other result types filtered by their own read permission | R2 |
| POST | `/learn/career/advice` | Role readiness and next steps | `tutor.conversation:use` (`self`, mode `career_coach`) | R2; `ai`; replaces `/career/advise` |
| GET | `/learn/announcements` | Announcements for the learner's cohorts | `self`, cohort member | R3 |
| GET | `/learn/threads` | Message threads the learner participates in | `messaging.message:send` (participant) | R3 |
| POST | `/learn/threads/{thread_id}/messages` | Reply in a thread | `messaging.message:send` (participant) | R3; Idempotency-Key |
| GET | `/learn/passport` | Learning passport preview | `learning.passport:export` (`self`) | R4 |
| POST | `/learn/passport/exports` | Export Open Badges 3.0 credentials and JSON transcript | `learning.passport:export` (`self`, `org_policy(passport_export)` for managed accounts) | R4; 202 |

### 5.3 `/orgs/{org_id}` — tenant administration and classrooms

All paths below are prefixed with `/orgs/{org_id}`. Audience is Instructor App and Institution App unless Notes narrow it to one.

**Organisation, structure, and people**

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET | `/` (the organisation) | Organisation profile, kind, status, defaults | `tenancy.organisation:read` | R3 |
| PATCH | `/` | Update name, default locale, time zone | `tenancy.organisation:edit` | R3; If-Match; Institution App |
| GET, POST | `/org-units` | List tree or create campus or department | `tenancy.organisation:read`, `tenancy.org_unit:edit` | R3 |
| GET, PATCH, DELETE | `/org-units/{unit_id}` | Read, rename, archive | `tenancy.organisation:read`, `tenancy.org_unit:edit` | R3; If-Match |
| POST | `/org-units/{unit_id}/move` | Move under another parent | `tenancy.org_unit:edit` at source and target | R3; depth rules (ADR 0015) |
| GET | `/members` | Members with status, roles, seats (filters `status`, `role`, `org_unit_id`, `q`) | `tenancy.membership:read` | R3 |
| GET, PATCH | `/members/{membership_id}` | Read, suspend, reactivate | `tenancy.membership:read`, `:end` | R3 |
| DELETE | `/members/{membership_id}` | End a membership | `tenancy.membership:end` | R3; managed accounts are suspended, not deleted |
| GET, POST | `/role-assignments` | List or grant a role at a scope in this organisation | `authz.role_assignment:read`, `:grant` (grantor must hold the role or `org_owner`; MFA ≤ 15 for org-level admin roles) | R3; Idempotency-Key |
| DELETE | `/role-assignments/{assignment_id}` | Revoke | `authz.role_assignment:revoke` | R3; last `org_owner` cannot be removed (409 `last-owner`) |
| GET, POST | `/invitations` | List or send invitations | `tenancy.membership:read`, `:invite` | R3; Idempotency-Key |
| DELETE | `/invitations/{invitation_id}` | Revoke | `tenancy.membership:invite` | R3 |
| POST | `/invitations/{invitation_id}/resend` | Resend | `tenancy.membership:invite` | R3 |
| GET, POST | `/enrolment-codes` | List or create join codes (scope, cohort, expiry, uses) | `tenancy.enrolment_code:create` | R3 |
| PATCH, DELETE | `/enrolment-codes/{code_id}` | Change or revoke | `tenancy.enrolment_code:create` | R3 |
| POST | `/uploads` | Get a write-only upload URL and `file_id` for an import or attachment | Permission of the intended use (`purpose` field) | R3; URL valid 15 min |
| POST | `/imports` | Bulk import members, cohort members, or staff from CSV or XLSX | `classroom.cohort_member:import` (cohort target, `is_cohort_staff` or org-unit scope) or `tenancy.membership:import` (organisation target) | R3; 202 job; Idempotency-Key |
| GET | `/imports/{import_id}` | Import detail with row outcomes | same as create | R3 |
| GET | `/jobs/{job_id}` | Job status | Permission of the job kind | R3 |
| POST | `/jobs/{job_id}/cancel` | Cancel | Permission of the job kind | R3 |

**Cohorts and plans**

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET, POST | `/cohorts` | List (filters `org_unit_id`, `staff=me`, `status`) or create | `classroom.cohort:read`, `classroom.cohort:create` | R3 |
| GET, PATCH | `/cohorts/{cohort_id}` | Read, update dates, settings | `classroom.cohort:read`, `:edit` (`is_cohort_staff` for instructors) | R3; If-Match |
| POST | `/cohorts/{cohort_id}/archive` | Archive at term end | `classroom.cohort:archive` | R3 |
| GET, POST | `/cohorts/{cohort_id}/members` | Roster or add learners | `classroom.cohort:read`, `classroom.cohort_member:add` | R3; more than 500 learners in one call is 202 |
| DELETE | `/cohorts/{cohort_id}/members/{membership_id}` | Remove a learner | `classroom.cohort_member:remove` | R3 |
| GET, POST | `/cohorts/{cohort_id}/staff` | Staff list or add instructor or TA | `classroom.cohort:read`, `classroom.cohort_staff:assign` (`lead_instructor` or org-unit admin) | R3 |
| DELETE | `/cohorts/{cohort_id}/staff/{staff_id}` | Remove staff | `classroom.cohort_staff:assign` | R3 |
| GET, POST | `/cohorts/{cohort_id}/plans` | List or create a plan pinned to a release | `classroom.cohort:read`, `classroom.cohort_plan:edit` (`is_cohort_staff`) | R3 |
| GET, PATCH | `/cohorts/{cohort_id}/plans/{plan_id}` | Read or edit draft plan | `classroom.cohort:read`, `classroom.cohort_plan:edit` | R3; If-Match |
| POST | `/cohorts/{cohort_id}/plans/{plan_id}/schedule` | Schedule (publish) the plan to learners | `classroom.cohort_plan:schedule` (`is_cohort_staff`) | R3; Idempotency-Key; emits `classroom.cohort_plan.scheduled` |
| POST | `/cohorts/{cohort_id}/plans/{plan_id}/repin` | Move the plan to a newer release | `classroom.cohort_plan:edit` | R3; returns a diff first with `dry_run=true` |
| GET, POST | `/cohorts/{cohort_id}/plans/{plan_id}/items` | Plan items | `classroom.cohort:read`, `classroom.cohort_plan:edit` | R3 |
| PATCH, DELETE | `/cohorts/{cohort_id}/plans/{plan_id}/items/{item_id}` | Change dates or remove | `classroom.cohort_plan:edit` | R3; If-Match |
| GET, PUT | `/cohorts/{cohort_id}/plans/{plan_id}/overlay` | Reorder, hide, supplement, instructions | `content.overlay:edit` (`is_cohort_staff`) | R3; If-Match; never changes the release |
| GET, POST | `/overlays` | Organisation-wide overlays for a release | `content.overlay:edit` (organisation or department scope) | R3 |
| GET, POST | `/cohorts/{cohort_id}/live-sessions` | Scheduled sessions | `classroom.cohort:read`, `classroom.live_session:edit` | R3 |
| GET, PUT | `/cohorts/{cohort_id}/live-sessions/{session_id}/attendance` | Read or record attendance | `classroom.attendance:read`, `:record` | R3 |
| GET | `/cohorts/{cohort_id}/risk-signals` | At-risk learners with evidence | `classroom.risk_signal:read` (`is_cohort_staff`) | R3 |
| GET, POST | `/cohorts/{cohort_id}/interventions` | Log and track interventions | `classroom.risk_signal:read`, `classroom.intervention:create` | R3 |
| PATCH | `/cohorts/{cohort_id}/interventions/{intervention_id}` | Update outcome | `classroom.intervention:create` | R3 |

**Assessment**

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET, POST | `/assessments` | List or create an assessment (from bank items or new) | `assessment.assessment:read`, `:create` | R3 |
| GET, PATCH | `/assessments/{assessment_id}` | Read or edit | `assessment.assessment:read`, `:edit` (explicit deny once any assignment is open) | R3; If-Match |
| GET, POST | `/assessments/{assessment_id}/items` | Items in the assessment | `assessment.assessment:edit` | R3 |
| GET, POST | `/rubrics` | List or create rubric with criteria and levels | `assessment.assessment:read`, `assessment.rubric:edit` | R3; Idempotency-Key |
| GET, PUT | `/rubrics/{rubric_id}` | Read or replace (versioned) | `assessment.assessment:read`, `assessment.rubric:edit` | R3; If-Match; in-use rubrics create a new version |
| GET, POST | `/assignments` | List (filters `cohort_id`, `status`, `due_from`) or create | `assessment.assessment:read`, `assessment.assignment:publish` (`is_cohort_staff`) | R3 |
| GET, PATCH | `/assignments/{assignment_id}` | Read or change dates and settings | `assessment.assessment:read`, `assessment.assignment:edit` | R3; If-Match |
| POST | `/assignments/{assignment_id}/publish` | Issue to learners | `assessment.assignment:publish` | R3; emits `assessment.assignment.published` |
| POST | `/assignments/{assignment_id}/close` | Close early | `assessment.assignment:edit` | R3 |
| GET, POST | `/assignments/{assignment_id}/accommodations` | Extra time, attempts, alternative dates per learner | `assessment.accommodation:edit` | R3 |
| GET | `/assignments/{assignment_id}/submissions` | Submissions with marking status | `assessment.submission:read` (`is_cohort_staff`) | R3 |
| GET | `/submissions/{submission_id}` | Submission with responses | `assessment.submission:read` | R3 |
| PUT | `/submissions/{submission_id}/marks` | Manual marks per criterion | `assessment.submission:mark` (`is_cohort_staff` or `is_ta_delegated(mark)`) | R3; If-Match |
| GET | `/submissions/{submission_id}/ai-proposals` | AI-proposed marks with rationale and evidence | `assessment.submission:mark` | R3; never visible in `/learn` |
| POST | `/submissions/{submission_id}/ai-proposals/{proposal_id}/accept` | Accept as the mark | `assessment.submission:mark` | R3; Idempotency-Key |
| POST | `/submissions/{submission_id}/ai-proposals/{proposal_id}/override` | Replace with human marks and reason | `assessment.grade:override` | R3; Idempotency-Key; MFA ≤ 60 if `org_policy(mfa_grading)`; may need approval |
| POST | `/assignments/{assignment_id}/ai-marking-runs` | Re-run AI marking (after rubric change) | `assessment.submission:mark`, `entitled(ai_marking)` | R3; 202 |
| GET | `/assignments/{assignment_id}/grades` | Grades by learner | `assessment.grade:read` (`is_cohort_staff`) | R3 |
| POST | `/assignments/{assignment_id}/grade-releases` | Release grades (all or listed learners) | `assessment.grade:release` (`is_cohort_staff`; TAs only with delegation) | R3; Idempotency-Key; 202 above 500 learners |
| POST | `/grades/{grade_id}/overrides` | Override a released or automatic grade | `assessment.grade:override` | R3; Idempotency-Key; reason required |
| POST | `/grade-overrides/{override_id}/approve` | Approve an override when policy requires | `assessment.grade_override:approve` (`lead_instructor`, `not_author`) | R3 |
| GET | `/cohorts/{cohort_id}/gradebook` | Gradebook grid | `assessment.grade:read` | R3 |
| POST | `/cohorts/{cohort_id}/gradebook/exports` | Export CSV or XLSX | `assessment.gradebook:export` | R3; 202 |

**Communication, analytics, and reports**

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET, POST | `/cohorts/{cohort_id}/announcements` | List or post | `classroom.cohort:read`, `messaging.announcement:create` | R3; Idempotency-Key |
| GET, POST | `/threads` | Staff threads with learners | `messaging.message:send` (participant) | R3 |
| POST | `/threads/{thread_id}/messages` | Send | `messaging.message:send` (participant) | R3; Idempotency-Key |
| GET | `/analytics/overview` | Organisation or org-unit KPIs (`org_unit_id`) | `analytics.dashboard:read` | R3; from rollups, `freshness` field |
| GET | `/analytics/cohorts/{cohort_id}` | Cohort progress, mastery, engagement | `analytics.dashboard:read` (`is_cohort_staff` or scope) | R3 |
| GET | `/analytics/learners/{membership_id}` | One learner's progress in this tenant | `learning.progress:read` (`consent_granted(learning_record)` for personal accounts) | R3 |
| GET | `/analytics/ai-usage` | AI usage and cost against quota | `ai.usage:read` | R3; Institution App |
| GET | `/report-definitions` | Available report types with parameters | `reporting.report:read` | R3 |
| POST | `/reports` | Run a report in a locale and format | Permission of the definition | R3; 202; Idempotency-Key |
| GET | `/reports/{report_id}` | Status and signed download link | Permission of the definition | R3 |
| GET, POST | `/report-schedules` | Scheduled reports and recipients | `reporting.report:schedule` | R3 |
| DELETE | `/report-schedules/{schedule_id}` | Remove | `reporting.report:schedule` | R3 |

**Commerce, configuration, integrations, compliance** (Institution App only)

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET | `/licences` | Licences, terms, entitlements, seat counts | `commerce.licence:read` | R3 |
| GET, POST | `/licences/{licence_id}/seat-assignments` | List or assign seats to memberships | `commerce.seat:assign` | R3; Idempotency-Key; 202 above 500 |
| DELETE | `/licences/{licence_id}/seat-assignments/{seat_id}` | Release a seat | `commerce.seat:assign` | R3 |
| GET | `/invoices`, `/invoices/{invoice_id}` | Invoices and PDFs | `commerce.invoice:read` | R3 |
| POST | `/billing-portal-sessions` | Stripe customer portal link | `commerce.payment_method:edit`, MFA ≤ 15 | R3 |
| GET, PUT | `/branding` | Logo, colours, display name, email sender name | `tenancy.branding:edit` | R3; If-Match; contrast validated (422 `branding-contrast`) |
| GET, POST | `/domains` | Verified domains (SSO routing, white-label) | `tenancy.domain:verify`, MFA ≤ 15 | R3 |
| POST | `/domains/{domain_id}/verify` | Check DNS TXT record | `tenancy.domain:verify` | R3 |
| DELETE | `/domains/{domain_id}` | Remove | `tenancy.domain:verify`, MFA ≤ 15 | R3 |
| GET, POST | `/sso-connections` | SSO connections (SAML or OIDC) and JIT rules | `tenancy.sso_connection:configure`, MFA ≤ 15 | R3 |
| PATCH, DELETE | `/sso-connections/{connection_id}` | Change or remove | `tenancy.sso_connection:configure`, MFA ≤ 15 | R3; If-Match |
| POST | `/sso-connections/{connection_id}/test` | Test sign-in flow | `tenancy.sso_connection:configure` | R3 |
| GET, PATCH | `/policies` | Organisation policy flags (leaderboards, AI modes, passport export, retention, IP allow-list, MFA for grading) | `tenancy.org_policy:edit` | R3; If-Match |
| GET, POST | `/webhook-endpoints` | Outbound webhook endpoints | `integration.webhook_endpoint:configure`, MFA ≤ 15 on create | R3; secret shown once |
| PATCH, DELETE | `/webhook-endpoints/{endpoint_id}` | Change events, disable, remove | `integration.webhook_endpoint:configure` | R3 |
| POST | `/webhook-endpoints/{endpoint_id}/rotate-secret` | New secret with 24 h overlap | `integration.webhook_endpoint:configure`, MFA ≤ 15 | R3 |
| GET | `/webhook-endpoints/{endpoint_id}/deliveries` | Delivery log | `integration.webhook_endpoint:configure` | R3 |
| POST | `/webhook-endpoints/{endpoint_id}/deliveries/{delivery_id}/redeliver` | Resend | `integration.webhook_endpoint:configure` | R3 |
| GET, POST | `/scim-clients` | SCIM clients; create returns token once | `integration.scim_client:configure`, MFA ≤ 15 | R4 |
| DELETE | `/scim-clients/{client_id}` | Revoke | `integration.scim_client:configure` | R4 |
| GET, POST | `/lti-platforms` | Register an LMS (issuer, client id, JWKS, endpoints) | `integration.lti_platform:configure` | R4 |
| GET, POST | `/lti-platforms/{platform_id}/deployments` | Deployment ids and cohort mapping | `integration.lti_platform:configure` | R4 |
| POST | `/lti-platforms/{platform_id}/deployments/{deployment_id}/roster-syncs` | Pull roster through NRPS | `integration.lti_platform:configure` | R4; 202 |
| GET, POST | `/oneroster-syncs` | Sync configurations and runs | `integration.oneroster_sync:configure` | R4 |
| POST | `/oneroster-syncs/{sync_id}/runs` | Run now (dry run supported) | `integration.oneroster_sync:configure` | R4; 202 |
| GET, POST | `/xapi-exports` | LRS endpoint and statement filters | `integration.xapi_export:configure` | R4 |
| GET, POST | `/compliance-requests` | Access, erasure, rectification requests for members | `audit.dsar:process` (`org_compliance_officer`), MFA ≤ 15 for erasure | R3; 202 |
| GET | `/compliance-requests/{request_id}` | Status and evidence | `audit.dsar:process` | R3 |
| GET | `/audit-events` | Organisation audit trail (filters `actor_id`, `action`, `from`, `to`) | `audit.log:read` | R3 |
| POST | `/audit-exports` | Export audit trail | `audit.log:export`, MFA ≤ 15 | R3; 202 |

### 5.4 `/content` — Content Studio

All paths are prefixed with `/content`. `{collection}` is one of `assets`, `lessons`, `modules`, `courses`, `paths`, `items`. Every edit requires `If-Match`. Audience: Content Studio only.

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET | `/workspaces` | Workspaces the person holds roles in | `content.item:read` | R2 |
| GET | `/workspaces/{workspace_id}` | Workspace detail, locales, settings | `content.item:read` | R2 |
| GET, POST | `/workspaces/{workspace_id}/role-assignments` | Workspace roles | `authz.role_assignment:read`, `:grant` (`platform_admin` or workspace owner) | R2 |
| DELETE | `/workspaces/{workspace_id}/role-assignments/{assignment_id}` | Revoke | `authz.role_assignment:revoke` | R2 |
| GET, POST | `/workspaces/{workspace_id}/assets` | List or create an asset (metadata) | `knowledge.asset:read`, `:upload` | R2; replaces `/admin/knowledge` |
| GET, PATCH | `/workspaces/{workspace_id}/assets/{asset_id}` | Read or edit metadata, rights, licence terms | `knowledge.asset:read`, `:edit` | R2 |
| POST | `/workspaces/{workspace_id}/assets/{asset_id}/versions` | New version; returns a write-only upload URL | `knowledge.asset:edit` | R2; Idempotency-Key |
| POST | `/workspaces/{workspace_id}/assets/{asset_id}/versions/{version}/uploaded` | Confirm upload; starts ingestion | `knowledge.asset:edit` | R2; 202 |
| GET | `/workspaces/{workspace_id}/assets/{asset_id}/versions` | Version history | `knowledge.asset:read` | R2 |
| GET | `/workspaces/{workspace_id}/assets/{asset_id}/versions/{a}/diff/{b}` | Text diff between versions | `knowledge.asset:read` | R2 |
| GET | `/workspaces/{workspace_id}/ingestion-jobs` | Ingestion jobs (filters `status`) | `knowledge.asset:read` | R2 |
| GET, POST | `/workspaces/{workspace_id}/lessons` | Lessons | `content.item:read`, `:create` | R2 |
| GET, PATCH, DELETE | `/workspaces/{workspace_id}/lessons/{lesson_id}` | Read, edit draft body per locale and style, delete draft | `content.item:read`, `:edit` | R2; If-Match |
| GET, POST | `/workspaces/{workspace_id}/modules` | Modules | `content.item:read`, `:create` | R2 |
| GET, PATCH | `/workspaces/{workspace_id}/modules/{module_id}` | Read, edit ordered contents | `content.item:read`, `:edit` | R2; If-Match |
| GET, POST | `/workspaces/{workspace_id}/courses` | Courses | `content.item:read`, `:create` | R2 |
| GET, PATCH | `/workspaces/{workspace_id}/courses/{course_id}` | Read, edit outcomes, prerequisites, structure | `content.item:read`, `:edit` | R2; If-Match |
| GET, POST | `/workspaces/{workspace_id}/paths` | Learning paths | `content.item:read`, `:create` | R2 |
| GET, PATCH | `/workspaces/{workspace_id}/paths/{path_id}` | Read, edit | `content.item:read`, `:edit` | R2; If-Match |
| GET, POST | `/workspaces/{workspace_id}/items` | Item bank (filters `concept`, `kind`, `difficulty`, `locale`, `status`) | `content.item:read`, `:create` | R2 |
| GET, PATCH | `/workspaces/{workspace_id}/items/{item_id}` | Read, edit item and answer key | `content.item:read`, `:edit` | R2; If-Match; answer keys never leave `/content` and `/orgs` marking views |
| POST | `/workspaces/{workspace_id}/{collection}/{id}/transitions` | Workflow transition (`in_review`, `approved`, `changes_requested`, `archived`) with comment | `content.item:submit`, `content.item:review` (`not_author`), `content.release:archive` | R2; If-Match; 409 `invalid-transition` |
| GET | `/workspaces/{workspace_id}/review-queue` | Items awaiting the caller's review | `content.item:review` | R2 |
| GET, POST | `/workspaces/{workspace_id}/{collection}/{id}/comments` | Review comments, anchored to a field or range | `content.item:edit` or `content.item:review` | R2 |
| PATCH | `/workspaces/{workspace_id}/comments/{comment_id}` | Resolve or edit | `content.item:edit` or `content.item:review` (`self` for edits) | R2 |
| GET | `/workspaces/{workspace_id}/courses/{course_id}/release-impact` | Impact of releasing the current head: version bump suggestion, affected cohorts and overlays, removed or changed items, locales not approved | `content.course:publish` | R2 |
| GET, POST | `/workspaces/{workspace_id}/releases` | List or publish a course or path release (immediate or scheduled) | `content.item:read`, `content.course:publish` or `content.path:publish` (`not_author` of the last change, MFA ≤ 15) | R2; Idempotency-Key; If-Match on the source head; emits `content.release.published` |
| GET | `/workspaces/{workspace_id}/releases/{release_id}` | Release detail, items, changelog | `content.item:read` | R2 |
| POST | `/workspaces/{workspace_id}/releases/{release_id}/archive` | Archive (no new pins; existing pins continue) | `content.release:archive` | R2; emits `content.release.archived` |
| POST | `/workspaces/{workspace_id}/derived-courses` | Derive an organisation copy from a master release | `content.derived_course:create` in an `org` workspace, `entitled(org_workspace)` | R3 |
| GET | `/workspaces/{workspace_id}/derived-courses/{course_id}/upstream-diff` | Changes in newer upstream releases | `content.item:read` | R3 |
| POST | `/workspaces/{workspace_id}/derived-courses/{course_id}/merges` | Merge selected upstream changes | `content.item:edit` | R3 |
| GET, POST | `/workspaces/{workspace_id}/taxonomy-nodes` | Taxonomy tree | `knowledge.asset:read`, `knowledge.taxonomy:edit` | R2 |
| PATCH, DELETE | `/workspaces/{workspace_id}/taxonomy-nodes/{node_id}` | Rename, move, remove | `knowledge.taxonomy:edit` (`knowledge_steward`) | R2 |
| GET, POST | `/workspaces/{workspace_id}/concepts` | Concepts | `knowledge.asset:read`, `knowledge.concept:edit` | R2 |
| PATCH | `/workspaces/{workspace_id}/concepts/{concept_id}` | Edit concept, labels per locale | `knowledge.concept:edit` | R2; If-Match |
| GET, POST | `/workspaces/{workspace_id}/concept-relations` | Typed, weighted edges | `knowledge.asset:read`, `knowledge.concept_relation:edit` | R2; 409 `cycle-detected` for prerequisite cycles |
| DELETE | `/workspaces/{workspace_id}/concept-relations/{relation_id}` | Remove edge | `knowledge.concept_relation:edit` | R2 |
| GET | `/workspaces/{workspace_id}/graph` | Subgraph around a concept or domain | `knowledge.asset:read` | R2 |
| GET, PUT | `/workspaces/{workspace_id}/metadata-schemas/{asset_kind}` | Metadata schema per asset kind | `knowledge.metadata_schema:edit` | R2; If-Match |
| GET, POST | `/workspaces/{workspace_id}/generation-jobs` | AI generation of drafts from asset versions | `content.item:generate`, `entitled(ai_generation)` | R2; 202; rate class `ai` |
| GET, POST | `/workspaces/{workspace_id}/localisation-jobs` | Machine-draft translations for items and locales | `content.translation:edit` | R2; 202 |
| GET, PATCH | `/workspaces/{workspace_id}/{collection}/{id}/translations/{locale}` | Read or edit a translation | `content.translation:edit` (`localisation_editor` for the locale) | R2; If-Match |
| POST | `/workspaces/{workspace_id}/{collection}/{id}/translations/{locale}/transitions` | Approve or reject a translation | `content.translation:approve` (`not_author`) | R2 |
| GET | `/workspaces/{workspace_id}/search` | Search assets, items, concepts in the workspace | `content.item:read`, `knowledge.asset:read` | R2 |
| GET | `/jobs/{job_id}` | Job status | Permission of the job kind | R2 |

### 5.5 `/platform` — platform governance (Admin App only)

All writes need MFA within 15 minutes. Reads of tenant data need `X-Access-Reason`; support agents also need `X-Support-Ticket`.

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET, POST | `/platform/organisations` | List or create organisations | `tenancy.organisation:read`, `:create` | R2 |
| GET, PATCH | `/platform/organisations/{org_id}` | Read, change kind, stamp, status | `tenancy.organisation:read`, `:edit` | R2; If-Match |
| POST | `/platform/organisations/{org_id}/suspend` and `/reactivate` | Suspend or reactivate | `tenancy.organisation:suspend` | R2; Idempotency-Key |
| GET | `/platform/users` | Search accounts (`q` by email hash, handle, id) | `identity.account:read` (`reason_recorded`; `ticket_ref` for `support_agent`) | R2; replaces `/admin/users` |
| GET, PATCH | `/platform/users/{user_id}` | Read, suspend, reactivate | `identity.account:read`, `:suspend` | R2 |
| GET, POST | `/platform/role-assignments` | Platform-scope roles and `master` workspace roles | `authz.role_assignment:read`, `:grant` (`platform_admin`) | R1; last `platform_admin` cannot be removed |
| DELETE | `/platform/role-assignments/{assignment_id}` | Revoke | `authz.role_assignment:revoke` | R1 |
| GET, POST | `/platform/plans` | Consumer and organisation plans | `commerce.plan:edit` (`finance_admin`) | R2 |
| GET, PATCH | `/platform/subscriptions` and `/platform/subscriptions/{subscription_id}` | Consumer subscriptions | `commerce.subscription:manage` (`finance_admin`; read only for `support_agent` with `ticket_ref`) | R2 |
| GET, POST | `/platform/licences` | Organisation licences | `commerce.licence:read`, `:edit` (`finance_admin`) | R3 |
| PATCH | `/platform/licences/{licence_id}` | Change seats, term, entitlements | `commerce.licence:edit` | R3; emits `commerce.licence.changed` |
| POST | `/platform/invoices/{invoice_id}/refunds` | Refund | `commerce.refund:issue` | R3; Idempotency-Key |
| GET, POST | `/platform/feature-flags` | Flags | `platform.feature_flag:edit` | R1 |
| PATCH | `/platform/feature-flags/{flag_key}` | Change default and rules | `platform.feature_flag:edit` | R1; If-Match |
| GET, PATCH | `/platform/settings` | Platform settings | `platform.setting:edit` (`platform_operator`) | R1 |
| GET, POST | `/platform/models` | Model registry | `ai.model:register` (`ai_admin`) | R2 |
| GET, PUT | `/platform/model-routes` | Tier routes and tenant overrides | `ai.model_route:edit` | R2; If-Match |
| GET, POST | `/platform/prompt-releases` | Prompt and policy releases | `ai.prompt_release:publish` | R2 |
| POST | `/platform/prompt-releases/{release_id}/promote` | Promote to an environment | `ai.prompt_release:publish` (passing eval run required) | R2; 409 `eval-gate-failed` |
| GET, POST | `/platform/eval-runs` | Evaluation runs and results | `ai.evaluation:run` | R2; 202 |
| GET | `/platform/moderation/flags` | Flagged tutor messages | `tutor.flagged_message:review` | R2; replaces `/admin/moderation` |
| POST | `/platform/moderation/flags/{flag_id}/resolve` | Resolve with outcome | `tutor.flagged_message:review` | R2 |
| GET | `/platform/audit-events` | Platform audit trail | `audit.log:read` (`security_auditor`, `platform_admin`) | R1 |
| GET | `/platform/security-events` | Security events | `audit.security_event:read` | R2 |
| GET | `/platform/authz/explain` | Decision trace for subject, permission, resource | `authz.decision_log:read` (`security_auditor`) | R2 |
| GET, POST | `/platform/reports` | Global reports (cross-tenant, de-identified) | `analytics.dashboard:read` (aggregates only) | R3; 202 |
| GET | `/platform/jobs/{job_id}` | Job status | Permission of the job kind | R1 |
| GET | `/platform/dead-letters` | Dead-lettered events and jobs by subscription | `platform.job:run` (`platform_operator`) | R1 |
| POST | `/platform/dead-letters/{message_id}/replay` | Replay one message | `platform.job:run` | R1; Idempotency-Key |

### 5.6 Integrations and standards endpoints

| Method | Path | Purpose | Permission | Notes |
| --- | --- | --- | --- | --- |
| GET, POST | `/lti/login` | OIDC third-party initiated login from the LMS | `public` (validated `iss`, `client_id`, `lti_deployment_id`) | R4 |
| POST | `/lti/launch` | Resource link launch, Deep Linking request | LTI `id_token` verified | R4; resolves tenant, account (JIT), cohort; redirects into the Learner App or Instructor App |
| GET | `/lti/jwks` | AI Mentor tool public keys | `public` | R4 |
| — | AGS (outbound) | Post scores to the platform's line items on `assessment.grade.released` | `system` | R4; uses `integration.lti_line_items` |
| — | NRPS (outbound) | Pull memberships for a context into the mapped cohort | `system` | R4; triggered by roster sync |
| GET | `/scim/v2/ServiceProviderConfig`, `/ResourceTypes`, `/Schemas` | SCIM discovery | SCIM token | R4; `bulk.supported = false`, `filter.supported = true`, `patch.supported = true` |
| GET, POST | `/scim/v2/Users` | List (filter `userName eq`) or create a managed account | SCIM token | R4; creates account, membership, `learner` role |
| GET, PUT, PATCH, DELETE | `/scim/v2/Users/{id}` | Read, replace, patch (including `active`), deprovision | SCIM token | R4; `DELETE` and `active=false` suspend the membership |
| GET, POST | `/scim/v2/Groups` | Groups mapped to cohorts or org units | SCIM token | R4; mapping configured per SCIM client |
| GET, PUT, PATCH, DELETE | `/scim/v2/Groups/{id}` | Membership changes | SCIM token | R4 |
| — | OneRoster 1.2 (outbound pull) | `orgs`, `classes`, `users`, `enrollments` from the SIS | `system` | R4; runs from `/orgs/{org_id}/oneroster-syncs` |
| — | xAPI (outbound) | Statements to the organisation's LRS | `system` | R4 |
| POST | `/api/v1/integrations/oauth/token` | Partner client credentials token | Client authentication (`private_key_jwt`) | R5 |
| POST | `/webhooks/stripe` | Stripe events | Signature | R1; live at `/api/v1/webhooks/stripe`; Front Door rewrite from `/webhooks/*` (v1 SAD 12.2) |
| POST | `/webhooks/clerk` | Clerk user events | Svix signature | R1; live at `/api/v1/webhooks/clerk` |

---

## 6. Worked examples

Headers common to every example are omitted after the first: `Authorization: Bearer <jwt>`, `Accept-Language`, `Content-Type: application/json`. Ids are shortened with `…` where length does not matter.

### 6.1 Bulk import learners into a cohort

```http
POST /api/v1/orgs/0192f1c4-7a2e-7c11-9a55-2f0d3c1b8e01/imports
Authorization: Bearer <jwt>
Idempotency-Key: 6d0f2e1a-7b3c-4f9e-9a21-1c2d3e4f5a6b
Accept-Language: en
Content-Type: application/json
```

```json
{
  "kind": "cohort_members",
  "target": { "cohort_id": "0192f1c4-8b10-7d02-8c3e-5a9e7f6d1c22" },
  "file_id": "0192f1c5-01aa-7e33-8d10-77c1a2b3c4d5",
  "options": {
    "create_managed_accounts": true,
    "send_invitations": true,
    "default_locale": "fr",
    "on_existing_member": "add_to_cohort"
  }
}
```

`file_id` comes from a prior `POST /orgs/{org_id}/uploads` that returned a write-only upload URL. Response:

```json
{
  "id": "0192f1c5-0e41-7a9b-b2d4-91f0c3e2aa10",
  "kind": "cohort_member_import",
  "status": "queued",
  "links": {
    "self": "/api/v1/orgs/0192f1c4-…/jobs/0192f1c5-0e41-7a9b-b2d4-91f0c3e2aa10",
    "import": "/api/v1/orgs/0192f1c4-…/imports/0192f1c5-0e40-7c01-a1b2-c3d4e5f6a7b8"
  }
}
```

When finished, `GET …/jobs/{job_id}` returns:

```json
{
  "id": "0192f1c5-0e41-7a9b-b2d4-91f0c3e2aa10",
  "status": "partially_succeeded",
  "progress": { "processed": 400, "total": 400 },
  "result": { "accounts_created": 352, "existing_members_added": 40, "invitations_sent": 352, "rejected": 8 },
  "errors_url": "https://…/tenants/0192f1c4-…/imports/0192f1c5-0e40-…/errors.csv?sig=…",
  "finished_at": "2026-10-13T14:53:12Z"
}
```

### 6.2 Schedule a cohort plan

```http
POST /api/v1/orgs/{org_id}/cohorts/{cohort_id}/plans
Idempotency-Key: 1f0e…
```

```json
{
  "title": "RL Foundations — Autumn 2026",
  "release_id": "0192e0aa-…",
  "time_zone": "Europe/London",
  "auto_update": "patch",
  "dimension_bounds": { "register": { "min": "academic" }, "depth": { "min": "intermediate", "max": "advanced" } },
  "items": [
    { "kind": "module", "ref_id": "0192e0ab-…", "release_on": "2026-10-20", "due_on": "2026-11-03" },
    { "kind": "assignment", "ref_id": "0192f0c1-…", "release_on": "2026-11-03", "due_on": "2026-11-10", "close_on": "2026-11-12" },
    { "kind": "live_session", "starts_at": "2026-10-22T14:00:00Z", "duration_minutes": 60, "title": "Bellman equations workshop" }
  ]
}
```

Response `201` with `ETag: "r1"` and `status: "draft"`. Then:

```http
POST /api/v1/orgs/{org_id}/cohorts/{cohort_id}/plans/{plan_id}/schedule
If-Match: "r1"
Idempotency-Key: 2a9c…
```

```json
{
  "id": "0192f1d0-…",
  "status": "scheduled",
  "release": { "id": "0192e0aa-…", "course_id": "0192e09f-…", "version": "2.0.3" },
  "learners_enrolled": 0,
  "enrolment_job": "/api/v1/orgs/{org_id}/jobs/0192f1d0-77…",
  "scheduled_at": "2026-10-13T15:02:00Z"
}
```

`auto_update: "patch"` lets the plan move to new patch releases automatically; minor and major updates need `repin`.

### 6.3 Create a rubric

```http
POST /api/v1/orgs/{org_id}/rubrics
Idempotency-Key: 9b1d…
```

```json
{
  "title": "Policy gradient essay",
  "locale": "en",
  "scoring": "points",
  "criteria": [
    {
      "key": "correctness",
      "title": "Technical correctness",
      "weight": 0.5,
      "concept_ids": ["0192d1…policy-gradient", "0192d1…reinforce"],
      "levels": [
        { "points": 0, "label": "Missing", "descriptor": "No derivation or a wrong one." },
        { "points": 5, "label": "Partial", "descriptor": "Correct idea, errors in the derivation." },
        { "points": 10, "label": "Full", "descriptor": "Correct derivation of the REINFORCE estimator with assumptions stated." }
      ]
    },
    {
      "key": "clarity",
      "title": "Clarity of explanation",
      "weight": 0.5,
      "levels": [
        { "points": 0, "label": "Unclear", "descriptor": "Hard to follow." },
        { "points": 10, "label": "Clear", "descriptor": "Logical structure, terms defined." }
      ]
    }
  ],
  "ai_marking": { "enabled": true, "require_evidence": true }
}
```

Response `201`, `ETag: "r1"`, with `id`, `version: 1`, and `max_points: 20`. A `PUT` on a rubric used by a published assignment creates version 2 and leaves existing marks on version 1.

### 6.4 Accept or override an AI mark proposal

`GET /api/v1/orgs/{org_id}/submissions/{submission_id}/ai-proposals` returns:

```json
{
  "items": [
    {
      "id": "0192f2aa-…",
      "rubric_id": "0192f1e2-…",
      "rubric_version": 1,
      "status": "pending",
      "total_points": 15,
      "criteria": [
        { "key": "correctness", "points": 5, "rationale": "Derives the log-derivative trick but drops the baseline term.", "evidence": [{ "response_id": "…", "quote": "∇J = E[∇ log π(a|s) G]" }], "confidence": 0.71 },
        { "key": "clarity", "points": 10, "rationale": "Clear structure with defined terms.", "evidence": [{ "response_id": "…", "quote": "We first define the return G_t…" }], "confidence": 0.86 }
      ],
      "model": { "route": "reasoning", "prompt_release": "marking.rubric@2026-10-01" },
      "created_at": "2026-10-13T15:20:00Z"
    }
  ],
  "next_cursor": null
}
```

Accept:

```http
POST /api/v1/orgs/{org_id}/submissions/{submission_id}/ai-proposals/0192f2aa-…/accept
Idempotency-Key: 4c2e…
```

```json
{ "feedback_to_learner": "Good structure. Revisit the baseline and why it reduces variance." }
```

Response `200`: `{ "mark_id": "…", "source": "ai_accepted", "total_points": 15, "grade_status": "unreleased" }`.

Override:

```http
POST /api/v1/orgs/{org_id}/submissions/{submission_id}/ai-proposals/0192f2aa-…/override
Idempotency-Key: 5d3f…
```

```json
{
  "criteria": [{ "key": "correctness", "points": 8 }],
  "reason": "The baseline is mentioned in the second paragraph; the proposal missed it.",
  "feedback_to_learner": "Correct derivation. Make the baseline step explicit."
}
```

Response `200`: `{ "mark_id": "…", "source": "ai_overridden", "total_points": 18, "override_id": "…", "approval": "not_required", "grade_status": "unreleased" }`. When the organisation requires approval, `approval` is `pending` and the grade cannot be released until a lead instructor approves.

### 6.5 Release grades

```http
POST /api/v1/orgs/{org_id}/assignments/{assignment_id}/grade-releases
Idempotency-Key: 7e4a…
```

```json
{ "learners": "all_marked", "notify": true, "message": "Grades and feedback are now available." }
```

Response `200` (or `202` with a job above 500 learners):

```json
{
  "id": "0192f2c0-…",
  "assignment_id": "0192f0c1-…",
  "released_count": 118,
  "skipped": { "unmarked": 4, "pending_override_approval": 1 },
  "released_at": "2026-10-13T16:00:00Z",
  "events": ["assessment.grade.released"]
}
```

A second call with a new key releases only grades that became ready since the first.

### 6.6 Publish a content release

Impact analysis first:

```http
GET /api/v1/content/workspaces/master/courses/0192e09f-…/release-impact
```

```json
{
  "current_release": "2.0.3",
  "suggested_bump": "minor",
  "suggested_version": "2.1.0",
  "changes": { "lessons_added": 2, "lessons_changed": 5, "lessons_removed": 0, "items_changed": 3, "items_removed": 0 },
  "cohorts_pinned": 38,
  "cohorts_auto_updating": 12,
  "overlays_affected": [{ "org_id": "0192f1c4-…", "cohort_id": "0192f1c4-8b10-…", "hidden_items_changed": 1 }],
  "locales": { "en": "approved", "fr": "approved", "es": "in_review" },
  "blocking": []
}
```

Publish:

```http
POST /api/v1/content/workspaces/master/releases
If-Match: "r42"
Idempotency-Key: 8f5b…
```

```json
{
  "source": { "type": "course", "id": "0192e09f-…" },
  "version": "2.1.0",
  "notes": "Adds actor-critic lessons; clarifies the policy gradient theorem.",
  "locales": ["en", "fr"],
  "publish_at": null
}
```

Response `201`:

```json
{
  "id": "0192f2d5-…",
  "course_id": "0192e09f-…",
  "version": "2.1.0",
  "state": "published",
  "locales": ["en", "fr"],
  "published_at": "2026-10-13T16:10:00Z",
  "published_by": "0192a001-…"
}
```

`If-Match` is the ETag of the course head that was reviewed; if someone edited it after approval the call fails with 412. `es` is excluded because its translation is not approved; including it would be 409 `translation-not-approved`.

### 6.7 Leaderboard query

```http
GET /api/v1/learn/leaderboards?scope=cohort&scope_id=0192f1c4-8b10-…&period=week&metric=xp&limit=10
X-Org-Id: 0192f1c4-7a2e-7c11-9a55-2f0d3c1b8e01
```

```json
{
  "scope": "cohort",
  "scope_id": "0192f1c4-8b10-…",
  "period": { "kind": "week", "key": "2026-W42", "ends_at": "2026-10-19T00:00:00Z" },
  "metric": "xp",
  "entries": [
    { "rank": 1, "display_name": "ada_l", "level": 9, "title": "Data Scientist", "score": 1240, "is_me": false },
    { "rank": 2, "display_name": "Learner-4f2a1c", "level": 7, "title": "Data Scientist", "score": 1105, "is_me": true }
  ],
  "me": { "rank": 2, "score": 1105, "percentile": 98.3 },
  "participants": 118,
  "visibility": "cohort_members"
}
```

`period` accepts `all`, `week`, `month`, or `season` (with `season_id`). `scope=organisation` is shown to users as "institution". Opted-out learners and, for `global` and `country`, managed accounts whose organisation has not opted in are excluded.

### 6.8 Tutor turn with mode and persona

```http
POST /api/v1/learn/tutor/conversations/0192f300-…/messages
Accept: text/event-stream
X-Org-Id: 0192f1c4-7a2e-7c11-9a55-2f0d3c1b8e01
Idempotency-Key: 3b7c…
```

```json
{
  "content": "Why does subtracting a baseline not bias the policy gradient?",
  "mode": "tutor",
  "technique": "socratic",
  "persona_id": "0192d900-…-calm-academic",
  "context": { "lesson_id": "0192e0b4-…", "concept_slug": "policy-gradient" },
  "locale": "fr"
}
```

```text
event: meta
data: {"conversation_id":"0192f300-…","message_id":"0192f301-…","mode":"tutor","technique":"socratic","persona_id":"0192d900-…-calm-academic","concept_slug":"policy-gradient","stage":"probe","locale":"fr","integrity_mode":false,"effective_dimensions":{"depth":"advanced","register":"academic"}}

event: token
data: {"t":"Commençons par l'espérance : "}

event: citations
data: [{"label":"[S1]","asset_id":"0192c0…","version":3,"release_id":"0192f2d5-…","title":"Policy Gradient Methods","locale":"en","url":"/library/…"}]

event: done
data: {"message_id":"0192f301-…","tokens_in":1912,"tokens_out":388,"grounded":true}
```

If an integrity-enabled assessment window is open and the mode is blocked, the request fails with 403 `integrity-mode-active`. If the mode is allowed but restricted, `meta.integrity_mode` is `true` and the policy limits disclosure. A turn that exceeds the tenant AI quota fails with 429 and `limit_scope: "ai_quota"` before any token is sent.

### 6.9 Assign seats

```http
POST /api/v1/orgs/{org_id}/licences/0192f100-…/seat-assignments
Idempotency-Key: c1d2…
```

```json
{
  "membership_ids": ["0192f1c6-…", "0192f1c7-…", "0192f1c8-…"],
  "on_conflict": "skip_existing"
}
```

```json
{
  "licence_id": "0192f100-…",
  "assigned": ["0192f1c6-…", "0192f1c7-…"],
  "skipped": [{ "membership_id": "0192f1c8-…", "reason": "already_assigned" }],
  "seats": { "total": 500, "assigned": 412, "available": 88 }
}
```

If the request would exceed available seats, nothing is assigned and the response is 409 `seat-limit-reached` with `available` in the problem body.

### 6.10 SCIM create user

```http
POST /scim/v2/Users
Authorization: Bearer scim_7Qy…
Content-Type: application/scim+json
```

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User", "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"],
  "userName": "a.mensah@uni-a.example",
  "externalId": "00u1abcd2EFGH3ijk4l5",
  "name": { "givenName": "Ama", "familyName": "Mensah" },
  "emails": [{ "value": "a.mensah@uni-a.example", "primary": true, "type": "work" }],
  "preferredLanguage": "fr",
  "active": true,
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": { "department": "Computer Science" }
}
```

Response `201`, `Location: https://api.<domain>/scim/v2/Users/0192f400-…`:

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "0192f400-…",
  "externalId": "00u1abcd2EFGH3ijk4l5",
  "userName": "a.mensah@uni-a.example",
  "active": true,
  "meta": { "resourceType": "User", "created": "2026-10-13T16:30:00Z", "lastModified": "2026-10-13T16:30:00Z", "version": "W/\"r1\"", "location": "https://api.<domain>/scim/v2/Users/0192f400-…" }
}
```

The account is `managed` in the SCIM client's organisation, with an `active` membership and a `learner` role. `department` maps to an org unit when the SCIM client's mapping says so. SCIM errors use the SCIM error schema (RFC 7644 section 3.12), not problem details, because SCIM clients expect it; `scimType: "uniqueness"` is returned for a duplicate `userName`.

---

## 7. Error catalogue

All types are `urn:ai-mentor:problem:<kind>`. The first three exist in the live API.

| Kind | Status | When | Extension members |
| --- | --- | --- | --- |
| `validation` | 422 | Body, query, or path fails schema or a domain rule on input | `errors[]` |
| `rate-limited` | 429 | A rate bucket or quota is exhausted | `limit_scope`, `retry_after_seconds` |
| `not-ready` | 503 | A dependency is unavailable (index, provider, Stripe) | `dependency` |
| `unauthenticated` | 401 | Missing, invalid, or expired token; unknown `azp` | — |
| `account-suspended` | 403 | The account is suspended | — |
| `wrong-app-audience` | 403 | The app may not call this root or operation | `allowed_apps` |
| `mfa-step-up-required` | 403 | Second factor older than the operation allows | `max_age_seconds` |
| `reauthentication-required` | 401 | The per-app idle or absolute session limit has passed (09 §4) | — |
| `forbidden` | 403 | The policy engine denied the request | `permission`, `reason_code` |
| `not-found` | 404 | Resource does not exist or must not be revealed | — |
| `tenant-required` | 400 | No tenant could be resolved for a tenant-scoped call | — |
| `tenant-mismatch` | 400 | `X-Org-Id` disagrees with `{org_id}` | — |
| `not-a-member` | 403 | No active membership in the requested organisation | — |
| `organisation-suspended` | 403 | The organisation is suspended | — |
| `wrong-stamp` | 421 | The organisation lives in another regional stamp (R4) | `origin` |
| `entitlement-required` | 403 | Plan or licence lacks the feature, or no seat | `entitlement` |
| `integrity-mode-active` | 403 | A blocked mentor mode or practice feature during an integrity window | `assignment_id`, `ends_at` |
| `managed-account` | 403 | Operation allowed only for personal accounts | — |
| `self-approval-forbidden` | 403 | The two-person rule blocks approval or publishing by the author | — |
| `conflict` | 409 | Generic state conflict (duplicate handle, existing membership) | — |
| `invalid-transition` | 409 | Workflow or state transition not allowed from the current state | `from`, `to`, `allowed[]` |
| `release-immutable` | 409 | Attempt to change a published release | — |
| `translation-not-approved` | 409 | Publishing or serving a locale whose translation is not approved | `locales[]` |
| `org-unit-depth-exceeded` | 422 | An org unit would exceed the allowed tree depth (SRS TEN-007) | `max_depth` |
| `cycle-detected` | 409 | A prerequisite edge would create a cycle | `path[]` |
| `dimension-locked` | 409 | Learner tries to change a locked or bounded dimension | `dimension`, `locked_by` |
| `assessment-window-closed` | 409 | Submission outside the window and no accommodation | `closes_at` |
| `seat-limit-reached` | 409 | Not enough seats for the request | `available` |
| `last-owner` | 409 | Removing the last `org_owner` or `platform_admin` | — |
| `eval-gate-failed` | 409 | Prompt release promotion without a passing eval run | `eval_run_id` |
| `idempotency-in-progress` | 409 | Same key is still being processed | — |
| `idempotency-key-reused` | 422 | Same key with a different body | — |
| `precondition-failed` | 412 | `If-Match` does not match | `current_etag` |
| `precondition-required` | 428 | `If-Match` missing on an edit that requires it | — |
| `payload-too-large` | 413 | Body or upload above the limit | `max_bytes` |
| `unsupported-media-type` | 415 | Upload type not accepted | `accepted[]` |
| `branding-contrast` | 422 | Branding colours fail WCAG 2.2 AA contrast | `pairs[]` |
| `deprecated-operation-sunset` | 410 | Called after the sunset date | `successor` |

`about:blank` with status 500 remains for unexpected failures; it carries `trace_id` and no other detail.

---

## 8. Event-to-webhook mapping

Organisations may subscribe to these event types. Each webhook payload is the CloudEvents envelope with the `data` fields listed. Subscribing requires `integration.webhook_endpoint:configure` plus the read permission shown, checked at registration and again at each delivery.

| Webhook event type | Domain event | `data` fields | Read permission checked |
| --- | --- | --- | --- |
| `tenancy.membership.activated` | same | `membership_id`, `account_id`, `account_type`, `org_unit_id` | `tenancy.membership:read` |
| `tenancy.membership.ended` | same | `membership_id`, `account_id`, `reason` | `tenancy.membership:read` |
| `classroom.cohort_member.added` | same | `cohort_id`, `membership_id` | `classroom.cohort:read` |
| `classroom.cohort_plan.scheduled` | same | `cohort_id`, `plan_id`, `release_id` | `classroom.cohort:read` |
| `learning.enrolment.created` | same | `enrolment_id`, `membership_id`, `release_id`, `cohort_id` | `learning.progress:read` |
| `learning.lesson.completed` | same | `membership_id`, `lesson_id`, `release_id`, `completed_at` | `learning.progress:read` (consent applies) |
| `assessment.assignment.published` | same | `assignment_id`, `cohort_id`, `opens_at`, `due_at` | `assessment.assessment:read` |
| `assessment.submission.submitted` | same | `submission_id`, `assignment_id`, `membership_id`, `submitted_at`, `late` | `assessment.submission:read` |
| `assessment.grade.released` | same | `grade_id`, `assignment_id`, `membership_id`, `score`, `max_score`, `released_at` | `assessment.grade:read` |
| `assessment.grade.overridden` | same | `grade_id`, `override_id`, `previous_score`, `score` | `assessment.grade:read` |
| `gamification.badge.earned` | same | `membership_id`, `badge_key`, `earned_at` | `learning.progress:read` (consent applies) |
| `commerce.licence.changed` | same | `licence_id`, `seats_total`, `term_end`, `entitlements[]` | `commerce.licence:read` |
| `commerce.seat.assigned` | same | `licence_id`, `membership_id` | `commerce.licence:read` |
| `content.release.published` | same, filtered to releases the organisation has pinned or licensed | `release_id`, `course_id` or `path_id`, `version` | `learning.catalogue:read` |
| `reporting.report.generated` | same | `report_id`, `definition`, `format`, `expires_at` | Permission of the definition |
| `audit.data_request.completed` | same | `request_id`, `kind`, `completed_at` | `audit.dsar:process` |

Not available as webhooks: `tutor.message.flagged`, `assessment.submission.ai_marked` (proposals are internal until a human acts), `gamification.xp.awarded` and `learning.mastery.changed` (volume; use reports or xAPI), and all `identity`, `authz`, and `ai_gateway` events.

Example delivery:

```http
POST https://hooks.uni-a.example/ai-mentor
webhook-id: 0192f2c0-1a2b-7c3d-8e4f-5a6b7c8d9e0f
webhook-timestamp: 1791900000
webhook-signature: v1,K5oZfzN95Z9UVu1EsfQmfVNQhnkZ2pj9o9NDN/H/pI4=
Content-Type: application/json
```

```json
{
  "specversion": "1.0",
  "id": "0192f2c0-1a2b-7c3d-8e4f-5a6b7c8d9e0f",
  "type": "com.aimentor.assessment.grade.released.v1",
  "source": "/orgs/0192f1c4-7a2e-7c11-9a55-2f0d3c1b8e01",
  "time": "2026-10-13T16:00:00Z",
  "tenantid": "0192f1c4-7a2e-7c11-9a55-2f0d3c1b8e01",
  "correlationid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "data": { "grade_id": "0192f2bf-…", "assignment_id": "0192f0c1-…", "membership_id": "0192f1c6-…", "score": 18, "max_score": 20, "released_at": "2026-10-13T16:00:00Z" }
}
```

`actorid` is removed from webhook payloads; receivers get the organisation as `source`.

---

## 9. SDK and client generation

| Client | Source | Generator | Notes |
| --- | --- | --- | --- |
| `@aimentor/api-client` (`packages/api-client`) | `docs/openapi.yaml` | `openapi-typescript` for types plus a thin typed `fetch` wrapper | Used by all five apps. Handles bearer token and `X-Org-Id` injection, `Idempotency-Key` generation, `If-Match` from cached ETags, cursor iteration, problem-detail parsing into typed errors, SSE reading for tutor turns. CI fails if regenerated output differs (ADR 0014) |
| Event types (`packages/events`, optional) | `docs/events/*.json` | `json-schema-to-typescript` | Only if frontends consume event types (ADR 0014 future considerations) |
| Mobile (R4) | Same OpenAPI file | Same TypeScript client in React Native, or Swift and Kotlin generators if native | No mobile-only endpoints |
| Partner SDKs (R5) | Public subset of the OpenAPI file (`x-audience: partner`) | `openapi-python-client`, `openapi-typescript` | Published with semantic versions; changelog tied to deprecation policy |

Rules:

- Every v2 operation in `openapi.yaml` carries `x-implementation`, `x-release` (R1–R5), `x-permission`, `x-conditions`, `x-audience` (app codes), and `x-rate-class`. A CI check compares `x-permission` with the route's `require(...)`.
- Operation ids are `<root>_<resource>_<action>` in snake case (`orgs_grade_releases_create`), stable across versions.
- Contract tests run the generated client against the API in CI for every `live` operation.

---

## 10. Mobile and partner API considerations

| Concern | Mobile clients (R4 Learner, R5 Instructor) | Partner API (R5) |
| --- | --- | --- |
| Identity | Clerk native SDK; each mobile app is an authorised party mapped to the `learner` or `instructor` audience | OAuth 2.0 client credentials; tokens bound to one organisation and a permission subset |
| Surface | Same `/me`, `/learn`, and `/orgs` operations | Read-mostly subset of `/orgs` (rosters, plans, grades, reports) and webhooks; no `/content` writes until the marketplace |
| Offline | Practice and flashcard reviews queue on device with idempotency keys and replay on reconnect; the server accepts reviews up to 72 h late with original timestamps, subject to anti-abuse rules | Not applicable |
| Bandwidth | ETags on catalogue and lessons; `?include=` to avoid round trips; compressed responses | Cursor pagination; bulk exports as jobs |
| Push | `POST /me/devices`; push through Azure Notification Hubs | Webhooks |
| Streaming | SSE over HTTP/2 for tutor turns; reconnect with `message_id` to fetch the final message | No streaming |
| Limits | Same per-user and per-tenant buckets | Separate `partner` class per client, configured per contract |
| Gateway | Front Door as today | Azure API Management in front of `/api/v1` partner operations (v1 SAD ADR-11 trigger) for keys, quotas, and developer portal |
| Versioning | Old app versions must keep working for 12 months; the API sends `Deprecation` headers the apps surface as an update prompt | 12-month deprecation window |

---

## 11. Mapping from v1 routes

v1 learner routes stay as deprecated aliases until the end of R2, then return 410. `/admin/*` routes are retired at the end of R2 (ADR 0013).

| v1 route (live or v1 contract) | v2 operation |
| --- | --- |
| `POST /chat`, `POST /chat/stream` | `POST /learn/tutor/conversations/{id}/messages` (create the conversation first, or send `conversation_id: null` to the alias) |
| `GET /conversations`, `GET /conversations/{id}` | `GET /learn/tutor/conversations`, `GET /learn/tutor/conversations/{id}` |
| `POST /agents/run` | `POST /learn/tutor/conversations/{id}/messages` with `mode` chosen by the client; intent routing stays inside the tutor |
| `POST /quiz/generate`, `POST /quiz/{id}/grade` | `POST /learn/practice/quizzes`, `POST /learn/practice/quizzes/{id}/attempts` |
| `POST /flashcards/generate`, `GET /flashcards/due`, `POST /flashcards/{id}/review` | `/learn/practice/flashcards…` |
| `GET /lab/projects`, `POST /lab/run`, `POST /lab/review` | `/learn/practice/lab/projects`, `/runs`, `/reviews` |
| `GET /dashboard`, `GET /progress`, `GET /recommendations` | `/learn/dashboard`, `/learn/progress`, `/learn/recommendations` |
| `GET /learning-paths`, `GET /learning-paths/{slug}`, `GET /knowledge-graph` | `/learn/catalogue`, `/learn/catalogue/paths/{id}` (slug accepted), `/content/workspaces/{ws}/graph` for staff; learners get the graph view inside `/learn/catalogue/paths/{id}?include=graph` |
| `POST /progress/lessons/{slug}/complete` | `POST /learn/lessons/{lesson_id}/completions` |
| `POST /study-plan/create`, `GET /study-plans` | `POST /learn/study-plans`, `GET /learn/study-plans` |
| `POST /research/documents`, `POST /research/analyze` | `/learn/research/documents`, `/learn/research/analyses` |
| `POST /career/advise` | `POST /learn/career/advice` |
| `GET /leaderboard` (public top 10) | Kept as is (public, guests); signed-in learners use `/learn/leaderboards` |
| `GET /me`, `PATCH /me`, `GET /me/export`, `DELETE /me` | Unchanged |
| `GET /admin/users`, `PATCH /admin/users/{id}` | `/platform/users`, `/platform/role-assignments` (role changes become assignments) |
| `GET /admin/analytics` | `/platform/reports` (platform), `/orgs/{org_id}/analytics/*` (organisation) |
| `/admin/knowledge…`, taxonomy, curriculum, graph, review | `/content/workspaces/{ws}/…` |
| `/admin/configuration`, `/admin/providers` | `/platform/settings`, `/platform/feature-flags`, `/platform/models`, `/platform/model-routes` |
| `/admin/audit`, `/admin/moderation` | `/platform/audit-events`, `/platform/moderation/flags` |
| `POST /billing/checkout` | Unchanged for consumers (`/learn` alias added in R2: `POST /learn/billing/checkout-sessions`) |
| `POST /webhooks/stripe`, `POST /webhooks/clerk` | Unchanged |

---

## 12. Appendix: names introduced by this document

These names are not in [README.md](README.md). They follow its conventions.

| Name | Kind |
| --- | --- |
| `X-Access-Reason`, `X-Support-Ticket`, `Idempotent-Replayed` | Request and response headers |
| `x-release`, `x-permission`, `x-conditions`, `x-audience`, `x-rate-class` | OpenAPI extensions (beside the existing `x-implementation`) |
| Problem kinds in section 7 other than `validation`, `rate-limited`, `not-ready` | Error types |
| Condition names `self`, `is_ta_delegated`, `window_open`, `released`, `consent_granted`, `seat_assigned`, `entitled`, `org_policy`, `reason_recorded`, `ticket_ref`, `public` (ADR 0016 already names `same_tenant`, `is_cohort_staff`, `not_author`, `mfa_within`, `app_audience`, `integrity_mode_off`) | ABAC conditions |
| Rate classes `bulk`, `platform`, `standards`, `partner` | Rate limiting |
| Job resource and statuses `queued`, `running`, `succeeded`, `partially_succeeded`, `failed`, `cancelled` | Async jobs |
| None. Every permission named in section 5 is in the catalogue of [10-rbac-matrix.md](10-rbac-matrix.md) section 3, which owns the list; operations on the caller's own records use the condition `self` | Permissions |
| Leaderboard scope value `organisation` (UX label "institution") and `competition`; `period` values `all`, `week`, `month`, `season` | API parameters |
| `/api/v1/integrations/oauth/token`, `/orgs/{org_id}/uploads`, `/learn/billing/checkout-sessions` | Endpoints |
| Translation status values `missing`, `machine_draft`, `in_review`, `approved` (README names only `approved`) | Enum |
| Plan `auto_update` values `none`, `patch`, `minor` | Enum |
