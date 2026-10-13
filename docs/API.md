# API

Base path `/api/v1`. The hand-written contract is [openapi.yaml](openapi.yaml) (OpenAPI 3.1), with request and response schemas, validation, errors, and rate limits. Operations marked `x-implementation: contract` are not routed yet.

Outside production the API serves a generated schema at `GET /docs` and `GET /openapi.json`, covering live routes only. Production serves neither. `GET /health` (liveness, always `{"status":"ok"}`) and `GET /ready` (database, Qdrant, and Redis reachable; otherwise 503) are on the root, not under `/api/v1`.

## Errors

Every error is RFC 9457 `application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "This quiz was already submitted. Generate a new one to retry.",
  "instance": "/api/v1/quiz/6c1d…/grade",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
}
```

`type` is `about:blank` unless a specific kind applies: `urn:ai-mentor:problem:validation` (with `errors[]` of `{path, message}`), `urn:ai-mentor:problem:rate-limited`, or `urn:ai-mentor:problem:not-ready`. Every response carries `X-Request-Id`; send your own (8–64 of `A-Z a-z 0-9 . _ -`) to correlate.

## Rate limits

Per user: 60 requests a minute, 20 a minute on AI routes (chat, quiz, research, lab, study plan, agents, career, flashcard generation), and 10 uploads an hour. Per address: 120 a minute before authentication. A 429 carries `Retry-After`, `RateLimit-Limit`, `RateLimit-Remaining`, and `RateLimit-Reset`. Health, readiness, and webhooks are exempt.

## Auth

Send `Authorization: Bearer <Clerk JWT>`. The token must be RS256 from the Clerk JWKS, from `CLERK_ISSUER`, unexpired, with `azp` in `CLERK_AUTHORIZED_PARTIES` (and `aud` equal to `CLERK_AUDIENCE` when set). A failed check is 401 with `WWW-Authenticate: Bearer`; an unreachable JWKS is 503. Staff (instructor, admin) also need a verified second factor in production, otherwise 403. Suspended accounts get 403.

In development and test only, `X-Dev-User-Id` may be `demo-student`, `demo-instructor`, `demo-admin`, or another id matching `^[A-Za-z0-9_-]{1,64}$`. The header cannot choose a role.

## Account

`GET /me` returns id, email, display name, role, handle, locale, time zone, country, leaderboard opt-out, subscription status, XP, level, and streak.

`PATCH /me` with any of `handle` (`^[A-Za-z0-9_]{3,24}$`, unique ignoring case; 409 if taken), `locale` (`en`, `fr`, `es`), `timezone` (IANA name; 422 otherwise), `country_code` (ISO 3166 alpha-2), `leaderboard_opt_out`.

`GET /me/export` returns the learner's profile, conversations with messages, quiz results, documents, code submissions, flashcards, study plans, mastery, and XP ledger as JSON.

`DELETE /me` erases the account (204): the Clerk user, Qdrant points, and PostgreSQL rows; the Stripe customer is anonymised. Returns 503 if a dependency could not be reached, and nothing is deleted locally in that case.

Public: `GET /health`, `GET /api/v1/learning-paths`, `GET /api/v1/knowledge-graph`, `GET /api/v1/lab/projects`, `GET /api/v1/leaderboard`. Path detail and every other learning route require a user.

## Tutor

`POST /chat`

```json
{ "message": "Teach me Reinforcement Learning", "mode": "socratic", "conversation_id": null }
```

`mode` is `socratic` or `direct`. Response: `conversation_id`, `mode`, `stage`, `concept_slug`, `reply.content`.

`GET /conversations` and `GET /conversations/{id}` return history for the current user.

`POST /agents/run` with `{ "message": "..." }` classifies intent. Career, plan, and quiz intents call the engine. Code and research intents point the learner at the lab or the research page. Anything else is a socratic chat turn.

## Practice

`POST /quiz/generate` `{ "concept_slug": "agent-environment", "difficulty": "beginner" }`

Difficulty is `beginner`, `intermediate`, `advanced`, `expert`, or `phd`. Questions include `id`, `kind`, `prompt`, `options`, `position`. They do not include the answer.

`POST /quiz/{id}/grade` `{ "answers": [{ "question_id": "...", "response": "B" }] }`

Returns `score`, `max_score`, and per-question `correct`, `feedback`, `explanation`. A quiz is graded once; a second submission is 409. While the lab is off, generated quizzes contain no coding items.

`POST /lab/run` and `POST /lab/review` `{ "code": "...", "project_slug": "tabular-q-learning" }`

Returns `status` (`ok`, `rejected`, or `error`), `stdout`, `stderr`, `review`. A passing run earns project XP once per project. Both return 503 when the lab is off, which is the production default until the isolated runner exists.

`GET /lab/projects` lists briefs and starter code.

## Study

`GET /dashboard` returns display name, role, XP, level, streak, mastery, strengths, developing, weaknesses, recommendations, path progress, badges, lessons completed, quizzes taken.

`GET /progress` returns XP and per-concept scores.

`POST /progress/lessons/{slug}/complete`

`GET /learning-paths` and `GET /learning-paths/{slug}`

`GET /knowledge-graph?domain=` returns nodes and a Mermaid diagram.

`GET /recommendations`

## Resource catalog

`GET /resources` searches published Knowledge Pack and imported records. Query: `q`, `domain` (category), `topic`, `skill`, `concept`, `difficulty`, `resource_type`, `provider`, `language`, `tag`, `limit`. Response `{ "items": [...], "next_cursor": null }`. Bodies are omitted.

`GET /resources/{id}` returns one published record, including metadata.

`POST /resources/{id}/progress` `{ "status": "saved"|"started"|"completed"|"dismissed", "rating": 1-5 }`.

`GET /catalog/facets`, `GET /catalog/recommendations`, `GET /catalog/graph?category=`.

`GET|PATCH /me/learning-preferences` stores goals, career, style, preferred types, languages, weekly minutes, and free-only.

Staff: `/admin/catalog/import`, `/admin/catalog/sources`, `/admin/catalog/jobs`, `/admin/catalog/duplicates`. See [Knowledge-Catalog.md](Knowledge-Catalog.md).

`POST /study-plan/create` `{ "goal": "..." }` and `GET /study-plans`

`POST /flashcards/generate` `{ "concept_slug": "q-learning" }`

`GET /flashcards/due`

`POST /flashcards/{id}/review` `{ "rating": 5 }` uses SM-2. The studio maps Again, Hard, Good, Easy to 1, 3, 4, 5.

`POST /career/advise`

`GET /leaderboard` (public) returns the top 10 learners: `rank`, `display_name` (the learner's handle or a stable `Learner-xxxxxx` pseudonym), `xp`, `level`, `streak_days`. Staff, suspended accounts, and opted-out learners are excluded.

## Research

`POST /research/documents` multipart field `file`. PDF, DOCX, Markdown, or text. 10 MB cap (413), 10 uploads an hour. Returns `status` `ready`, or `unindexed` when the search index was unavailable.

`POST /research/analyze` `{ "document_id": "...", "question": "..." }`

Returns `mode` (`extractive` or `model`), `summary`, `excerpts`, `equations`, and `critique`, `gaps`, `future_work` which are null on an extractive pass.

## Admin and billing

Every `/admin/*` route requires at least the instructor role; a student gets 403 before the body is read.

`GET /admin/users` and `PATCH /admin/users/{id}` `{ "role": "instructor", "reason": "..." }` require admin. Changing your own role or demoting the last admin is 409; an unknown role is 422. Each change is audited with the previous and new role.

`GET /admin/analytics` requires instructor or admin. The curated library (`/admin/assets…`), taxonomy, overview, configuration, providers, audit, and moderation routes are described in [Admin.md](Admin.md). Publishing needs an admin. Approving your own submission is refused unless `CONTENT_SELF_APPROVAL` is on; when it is, the approval is flagged in the audit log. If the search index is unavailable, publishing fails with 503 and the asset stays approved.

`POST /billing/checkout` `{ "tier": "pro", "success_url": "...", "cancel_url": "..." }` returns 503 until Stripe is configured. Each return URL must match an entry of `STUDIO_ORIGINS` (default: the first CORS origin) exactly in scheme, host, and port; otherwise 400.

`POST /webhooks/stripe` and `POST /webhooks/clerk` verify provider signatures (400 otherwise) and return `{"received": true, "outcome": ...}`, where the outcome is `applied`, `duplicate`, `stale`, `ignored`, or `unmatched`. Each event id is applied once. Stripe events older than the last one applied to the account are ignored. Clerk `user.created` and `user.updated` refresh email and name and never the role. `user.deleted` erases the learner.
