# API

Base path `/api/v1`. The hand-written contract is [openapi.yaml](openapi.yaml) (OpenAPI 3.1), with request and response schemas, validation, errors, and rate limits. Operations marked `x-implementation: contract` are not routed yet.

The running API serves a generated schema at `GET /docs` and `GET /openapi.json`. That schema covers live routes only. `GET /health` is on the root, not under `/api/v1`.

Errors are `{"detail": "..."}` with 4xx or 5xx.

## Auth

Send `Authorization: Bearer <Clerk JWT>` in production. In development and test, `X-Dev-User-Id` may be `demo-student`, `demo-instructor`, `demo-admin`, or another id matching `^[A-Za-z0-9_-]{1,64}$`. The header cannot choose a role.

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

Returns `score`, `max_score`, and per-question `correct`, `feedback`, `explanation`.

`POST /lab/run` and `POST /lab/review` `{ "code": "...", "project_slug": "tabular-q-learning" }`

Returns `status` (`ok`, `rejected`, or `error`), `stdout`, `stderr`, `review`.

`GET /lab/projects` lists briefs and starter code.

## Study

`GET /dashboard` returns display name, role, XP, level, streak, mastery, strengths, developing, weaknesses, recommendations, path progress, badges, lessons completed, quizzes taken.

`GET /progress` returns XP and per-concept scores.

`POST /progress/lessons/{slug}/complete`

`GET /learning-paths` and `GET /learning-paths/{slug}`

`GET /knowledge-graph?domain=` returns nodes and a Mermaid diagram.

`GET /recommendations`

`POST /study-plan/create` `{ "goal": "..." }` and `GET /study-plans`

`POST /flashcards/generate` `{ "concept_slug": "q-learning" }`

`GET /flashcards/due`

`POST /flashcards/{id}/review` `{ "rating": 5 }` uses SM-2. The studio maps Again, Hard, Good, Easy to 1, 3, 4, 5.

`POST /career/advise`

`GET /leaderboard` returns display name, XP, level, and streak only.

## Research

`POST /research/documents` multipart field `file`. PDF, DOCX, Markdown, or text. 10 MB cap.

`POST /research/analyze` `{ "document_id": "...", "question": "..." }`

Returns `mode` (`extractive` or `model`), `summary`, `excerpts`, `equations`, and `critique`, `gaps`, `future_work` which are null on an extractive pass.

## Admin and billing

`GET /admin/users` and `PATCH /admin/users/{id}` `{ "role": "instructor" }` require admin. The last admin cannot be demoted.

`GET /admin/analytics` requires instructor or admin.

`POST /billing/checkout` `{ "tier": "pro", "success_url": "...", "cancel_url": "..." }` returns 503 until Stripe is configured. Return URLs must match `CORS_ORIGINS`.

`POST /webhooks/stripe` and `POST /webhooks/clerk` verify provider signatures. User deletion from Clerk is not implemented.
