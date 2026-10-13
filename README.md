# AI Mentor

AI Mentor is a learning studio for artificial intelligence, machine learning, reinforcement learning, robotics, and LLM engineering. The tutor opens with a question. Quizzes are graded from authored answer keys. An uploaded paper is quoted, and a critique appears only when the model cites a chunk from that file.

The Learner App and the staff admin portal are Next.js applications. The mentor is **one FastAPI service**, backed by PostgreSQL, Qdrant, and Redis. Instructors, institution administrators, and content teams will each get their own frontend on that same API; they are not extra roles inside the learner UI.

## Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Local Setup](#local-setup)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Running Locally](#running-locally)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Folder Structure](#folder-structure)
12. [Contribution Guidelines](#contribution-guidelines)
13. [License](#license)

## Overview

A learner picks a track, talks with the tutor, and practises with quizzes, flashcards, and a restricted Python lab. Progress is a mastery score per concept. Recommendations follow the prerequisite graph, so a new learner starts at the roots of the catalog.

Four tracks ship in the catalog: AI Fundamentals, Reinforcement Learning, Robotics, and LLM Engineering. The curriculum source is `backend/app/domain/catalog.py`. Restarting the API refreshes catalog rows and leaves learner progress in place.

Identity is Clerk. Roles (`student`, `instructor`, `admin`) are stored in Postgres and never read from a token. The first admin is granted from the command line (`make grant-admin`). In development, a session switcher sends `X-Dev-User-Id`. Production refuses that header, and a production frontend build fails if it is enabled.

AI Mentor is growing into a learning ecosystem of five applications on one platform: the Learner App (this repository's `frontend/`), an Instructor App, an Institution App, the Admin App, and Content Studio, serving many organisations. That direction, and everything not built yet, is documented in [docs/platform](docs/platform/README.md), starting with the [gap analysis](docs/platform/00-gap-analysis.md) and the [roadmap](docs/platform/15-roadmap.md). The sections below describe the code that runs today.

The original product brief is in [Requirements.md](docs/Requirements.md). The knowledge-portal brief is in [Admin.md](docs/Admin.md). Engineering notes:

- [Architecture](docs/Architecture.md)
- [Documentation standards](docs/Documentation-Standards.md)
- [API](docs/API.md) and the OpenAPI contract [docs/openapi.yaml](docs/openapi.yaml)
- [Database](docs/Database.md)
- [Deployment](docs/Deployment.md)
- [Security](docs/Security.md) and the normative [Security-Compliance](docs/Security-Compliance.md)
- [Runbook](docs/Runbook.md)
- [Roadmap](docs/Roadmap.md)

## Features

| Surface | What it does |
| --- | --- |
| Landing | Tracks, pricing, illustrative scenarios, and an FAQ |
| Dashboard | Mastery bands, path progress, recommendations, XP, streaks, and badges |
| Tutor | Socratic or direct chat. Opening turns stay on the catalog script |
| Quiz | Authored items, graded on the server. The answer key is not in the quiz payload |
| Paths | Lesson markdown, prerequisites, and completion |
| Concept map | Prerequisite graph, with a text list beside the diagram |
| Flashcards | SM-2 reviews: Again, Hard, Good, Easy |
| Coding lab | Allowlisted Python, a GridWorld harness, then a written review. Off in production until the isolated runner exists |
| Research | PDF, DOCX, Markdown, or text, up to 10 MB. Embedded once, searched per question. Extractive until a model cites a chunk |
| Career | Role readiness from the learner's mastery map |
| Leaderboard | Top 10 by XP under a handle or pseudonym. Learners can opt out |
| Account | Profile settings, data export, and account erasure (`/api/v1/me`) |
| Admin portal | Curated library with review, four-eyes approval, and publishing into the tutor's search; users and roles; audit log; analytics |
| Billing | Stripe Checkout. Returns 503 until price and secret keys are set. Subscription state changes only from signed webhooks |

XP follows SRS GAM-002. Each lesson, quiz, project, review, and analysis pays once, with per-day limits, a daily cap of 400 on the learner's local day, and a level of `1 + xp // 250`. Chat updates the streak and does not grant XP.

## Architecture

Teaching rules live in `backend/app/domain` and do not import FastAPI or SQLAlchemy. HTTP handlers validate input and call the mentor engine. Agents are classes in that one process.

```mermaid
flowchart LR
  Learner["Learner App :3000"]
  Admin["Admin portal :3001"]
  API["FastAPI /api/v1"]
  Engine["Mentor engine and admin portal"]
  Domain["Domain policies"]
  Agents["Tutor, quiz, planner, research, coding, career"]
  Models["OpenAI, Anthropic, Gemini"]
  PG["PostgreSQL"]
  QD["Qdrant"]
  RD["Redis"]

  Learner -->|Bearer JWT| API
  Admin -->|Bearer JWT| API
  API --> RD
  API --> Engine
  Engine --> Domain
  Engine --> Agents
  Agents --> Models
  Engine --> PG
  Engine --> QD
```

Three more frontends share this API when they ship: Instructor App (`teach.`, :3002), Institution App (`org.`, :3003), Content Studio (`studio.`, :3004). See [ADR 0013](docs/adr/0013-five-applications-shared-platform.md).

With no model API key, the tutor still answers from the authored curriculum. With `QDRANT_URL` set to an HTTP address, vectors go to Qdrant and an OpenAI key is required for embeddings. Otherwise, in development only, a local store keeps deterministic hash vectors in Postgres.

Interactive API docs for a development process: [http://localhost:8000/docs](http://localhost:8000/docs). Production serves no docs.

## Tech Stack

| Layer | Choice |
| --- | --- |
| Learner App and admin portal | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Learner App data | TanStack Query, Zustand |
| Auth | Clerk |
| API | FastAPI, Python 3.12, Pydantic v2, Uvicorn |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Vectors | Qdrant. A local hash store in development when Qdrant is unset |
| Rate limits | Redis |
| Models | OpenAI, Anthropic, Gemini |
| Payments | Stripe |
| Observability | OpenTelemetry, Langfuse |
| Frontend hosting | Vercel |
| API hosting | One container image. Azure Container Apps is the primary host. AWS pulls the same image from GHCR |

## Local Setup

Install these before the project dependencies:

| Tool | Version |
| --- | --- |
| Python | 3.12 or newer |
| Node.js | 22 |
| npm | Comes with Node 22 |
| Docker Compose | Optional. Used by `make up` for PostgreSQL, Qdrant, and Redis |
| Make | Optional. The commands below also work without it |

`make api` and `make test` expect a virtualenv at the repository root, named `.venv`.

Docker is optional. Without it, run the API against SQLite as shown in [Running Locally](#running-locally).

## Installation

From the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e "./backend[dev]"
cd frontend && npm ci && cd ..
cd admin && npm ci && cd ..
```

`pip install -e "./backend[dev]"` installs the API and the development tools (`pytest`, `ruff`, `bandit`, `pip-audit`). `npm ci` installs each app from its lockfile.

## Configuration

The API reads environment variables and, when present, `backend/.env`. Create that file only for values you want to override. Empty optional values are treated as unset.

### API

The full list, with comments, is [.env.example](.env.example). The ones you are most likely to set:

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | `development`, `test`, or `production` |
| `DEV_AUTH` | on in development and test | Accept `X-Dev-User-Id`. Refused in production |
| `DATABASE_URL` | `postgresql+psycopg://mentor:mentor@localhost:5432/mentor` | SQLAlchemy URL. SQLite is allowed outside production |
| `QDRANT_URL` / `QDRANT_API_KEY` | `memory` / unset | `http(s)://...` uses Qdrant. Any other value uses the local store |
| `REDIS_URL` | unset | Shared rate-limit counters. Without it, limits are per process |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:3001` | Studio and admin origins |
| `STUDIO_ORIGINS` | first CORS origin | Allowed Stripe return origins, matched exactly |
| `CLERK_JWKS_URL`, `CLERK_ISSUER` | unset | Token verification |
| `CLERK_AUTHORIZED_PARTIES` | the CORS origins | Allowed `azp` values |
| `CLERK_AUDIENCE` | unset | Checked when set |
| `CLERK_SECRET_KEY` | unset | Deletes the Clerk user on account erasure |
| `CLERK_WEBHOOK_SECRET` | unset | Verifies `POST /api/v1/webhooks/clerk` |
| `REQUIRE_STAFF_MFA` | on in production | Staff calls need a second factor |
| `LAB_ENABLED` | off in production | The code lab. Production refuses to turn it on |
| `CONTENT_SELF_APPROVAL` | off | Lets an author approve their own library item, flagged in the audit log |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | unset | Model providers. OpenAI also provides embeddings |
| `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES` | `20`, `1` | Per model call |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_RESEARCH` | unset | Checkout stays 503 until set |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | unset | Model-call tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | OTLP/HTTP collector for traces |
| `RATE_LIMIT_PER_MINUTE`, `AI_RATE_LIMIT_PER_MINUTE`, `UPLOAD_RATE_LIMIT_PER_HOUR`, `ANONYMOUS_RATE_LIMIT_PER_MINUTE` | `60`, `20`, `10`, `120` | Per user, except the anonymous limit, which is per address |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Container only: proxies trusted for `X-Forwarded-For` |

Production startup fails if dev auth is on, Clerk verification or the Clerk secret is missing, `DATABASE_URL` is not PostgreSQL, Qdrant is not `https://` with a key, Redis or an OpenAI key is missing, the lab is on, staff MFA is off, or any origin is not explicit `https://`.

### Studio and admin

Copy `frontend/.env.example` to `frontend/.env.local`, and `admin/.env.example` to `admin/.env.local`:

| Variable | Local value | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API origin |
| `NEXT_PUBLIC_DEV_AUTH` | `true` | Shows the Demo student, instructor, and admin switcher. A production build fails if it is set |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | empty locally | Turns on Clerk sign-in and route protection. A production build fails without it |
| `CLERK_SECRET_KEY` | empty locally | Server-side Clerk key for the middleware |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/sign-in` | |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/sign-up` | Studio only |
| `NEXT_PUBLIC_ADMIN_URL` / `NEXT_PUBLIC_STUDIO_URL` | `http://localhost:3001` / `http://localhost:3000` | Links between the two apps |

A production build is one where `DEPLOY_ENV` or `VERCEL_ENV` is `production`.

Do not commit `.env`, `.env.local`, or API keys.

## Running Locally

Two processes. In one terminal:

```bash
make api
```

`make api` listens on `127.0.0.1:8000` and uses the default PostgreSQL URL. Start Postgres and run `make migrate` first, or point the API at SQLite:

```bash
cd backend
DATABASE_URL=sqlite:///./dev.sqlite APP_ENV=development ../.venv/bin/uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
make web
```

Open [http://localhost:3000](http://localhost:3000). The API health check is [http://localhost:8000/health](http://localhost:8000/health). The admin portal is a separate app:

```bash
make admin
```

It listens on [http://localhost:3001](http://localhost:3001). Local sessions default to Demo admin.

With PostgreSQL, `make migrate` applies the Alembic migrations and seeds the catalog and demo accounts. With SQLite, development startup creates the tables and seeds instead. Learner progress is kept across restarts.

The session switcher is visible when `NEXT_PUBLIC_DEV_AUTH=true`. The API accepts `X-Dev-User-Id` in development and refuses it in production. A new dev user is always a student. The header cannot grant a role.

The whole backend together:

```bash
make up
```

That Compose file runs Postgres 16 (`mentor` / `mentor`, database `mentor`), Qdrant, Redis, a one-off migrate job, and the API on port 8000 with dev auth enabled. Every port is bound to `127.0.0.1`. Do not publish that stack to the internet. Stop it with `make down`. The frontends are still `make web` and `make admin`.

To make a Clerk user the first admin (the command is audited):

```bash
make grant-admin CLERK_ID=user_123 REASON="founding admin"
```

## Testing

Unit tests cover `backend/app/domain`, where coverage must stay at or above 90 percent. Integration tests cover the HTTP surface, including authentication, cross-user access, the admin gate, XP idempotency, webhooks, and erasure.

```bash
make test       # SQLite, fast
make test-pg    # the same suite against migrated PostgreSQL (PG_URL)
make lint       # Ruff check and format check on app, tests, and alembic
make lint-migrations  # squawk on every migration after the frozen baseline
make audit      # pip-audit, bandit, npm audit
```

Frontend checks, in `frontend/` and `admin/`:

```bash
npm run typecheck
npm run build
```

GitHub Actions (`.github/workflows/ci.yml`) runs lint and tests on SQLite and on PostgreSQL 16, checks migrations against the models, verifies the target database schema, scans for secrets and vulnerable dependencies, builds both frontends, and asserts that a production build with dev auth fails.

## Deployment

The studio and admin portal deploy to Vercel as separate projects. The API is one image, built from `backend/Dockerfile` (Python 3.12, non-root user `mentor`, Uvicorn on `0.0.0.0:8000` behind trusted proxies). Migrations do not run in the web process: run `python -m app.cli migrate` from the same image as a one-off job before each rollout.

`.github/workflows/publish.yml` pushes that image to GHCR on a `v*` tag or a manual run. It does not deploy on every push. Azure Container Apps is the primary API host. AWS ECS or App Runner can pull the same image.

Before a public deploy, set the Clerk keys and leave `NEXT_PUBLIC_DEV_AUTH` empty; the build refuses otherwise. Put secrets in the host secret store. Operator notes are in [docs/Deployment.md](docs/Deployment.md). The Azure layout, pipelines, backups, and recovery targets are in [docs/Infrastructure.md](docs/Infrastructure.md).

## Folder Structure

```text
AI-Mentor/
├── backend/
│   ├── app/
│   │   ├── api/            # /api/v1 routes
│   │   ├── agents/         # Tutor, quiz, research, coding, planner, career
│   │   ├── core/           # Settings, database, auth, rate limit, telemetry
│   │   ├── domain/         # Teaching rules, grading, mastery, XP, catalog
│   │   ├── models/         # SQLAlchemy entities
│   │   ├── prompts/        # Instructions composed into model calls
│   │   ├── middleware/     # Request id, security headers, address rate limit
│   │   ├── repositories/
│   │   ├── services/       # Mentor engine, admin portal, retrieval, privacy, webhooks, model router
│   │   └── cli.py          # migrate, seed, seed-pack, grant-admin, reapply-erasures
│   ├── alembic/            # Schema migrations
│   ├── db/                 # Target database schema (ADR 0011, proposed)
│   ├── tests/unit/
│   ├── tests/integration/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/               # Learner App today (target apps/learner)
│   ├── app/                # Landing page and learner routes
│   ├── components/
│   ├── lib/
│   ├── stores/
│   └── Dockerfile
├── admin/                  # Staff portal today: operations + content (splits into Admin App and Content Studio)
├── infrastructure/
│   └── compose.yaml        # Postgres, Qdrant, Redis, migrate job, and the API
├── seed-data/              # Knowledge Pack v1.0 JSON (make write-pack)
├── docs/                   # Architecture, API, OpenAPI, database, deployment
├── .github/workflows/      # CI and image publish
└── Makefile
```

Learner App routes live under `frontend/app/(studio)/` until the R1 rename: dashboard, tutor, quiz, paths, catalog, graph, flashcards, lab, research, and a link to admin. Target apps (`apps/learner`, `apps/instructor`, `apps/institution`, `apps/admin`, `apps/studio`) are specified in [docs/platform](docs/platform/README.md). The Resource Catalog that runs today is [Knowledge-Catalog.md](docs/Knowledge-Catalog.md).

## Contribution Guidelines

Open a pull request against the main branch. Keep the change focused on one behavior.

- Put teaching decisions in `backend/app/domain`. Routes validate and delegate.
- Keep domain coverage at or above 90 percent. Run `make test` and `make lint` before you push.
- For frontend changes, run `npm run typecheck` and `npm run build` in `frontend/` or `admin/`.
- Schema changes need an Alembic revision; `alembic check` in CI fails on drift.
- If you add or change an HTTP route, update [docs/openapi.yaml](docs/openapi.yaml) and [docs/API.md](docs/API.md). Mark a route `live` only when the handler exists.
- Do not commit `.env` files, API keys, `dev.sqlite`, or `frontend/.next`.
- Ruff line length is 100. Follow [docs/Documentation-Standards.md](docs/Documentation-Standards.md) for docstrings, TypeDoc comments, and API notes.
- Describe the behavior a reviewer can verify. Screenshots help for studio layout changes.

CI must pass. A drop below the coverage gate fails the backend job.

## License

This repository does not include a `LICENSE` file. All rights are reserved. Do not copy or redistribute the code until the maintainers add a license.
