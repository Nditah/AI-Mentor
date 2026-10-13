# AI Mentor

AI Mentor is a learning studio for artificial intelligence, machine learning, reinforcement learning, robotics, and LLM engineering. The tutor opens with a question. Quizzes are graded from authored answer keys. An uploaded paper is quoted, and a critique appears only when the model cites a chunk from that file.

The studio is a Next.js application. The mentor is one FastAPI service, backed by PostgreSQL and an optional Qdrant index.

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

Identity is Clerk. Roles (`student`, `instructor`, `admin`) are stored in Postgres. In development, a session switcher sends `X-Dev-User-Id`. Production refuses that header.

The product vision is in [Requirements.md](docs/Requirements.md). The knowledge-portal brief is in [Admin.md](docs/Admin.md). Engineering notes:

- [Architecture](docs/Architecture.md)
- [Documentation standards](docs/Documentation-Standards.md)
- [API](docs/API.md) and the OpenAPI contract [docs/openapi.yaml](docs/openapi.yaml)
- [Database](docs/Database.md)
- [Deployment](docs/Deployment.md)
- [Security](docs/Security.md)
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
| Coding lab | Allowlisted Python, a GridWorld harness, then a written review |
| Research | PDF, DOCX, Markdown, or text, up to 10 MB. Extractive until a model cites a chunk |
| Career | Role readiness from the learner's mastery map |
| Admin | Learner list for admins. Analytics for instructors and admins |
| Billing | Stripe Checkout. Returns 503 until price and secret keys are set |

XP is capped at 400 per day. A level is `1 + xp // 250`. Chat updates the streak and does not grant XP.

## Architecture

Teaching rules live in `backend/app/domain` and do not import FastAPI or SQLAlchemy. HTTP handlers validate input and call the mentor engine. Agents are classes in that one process.

```mermaid
flowchart LR
  Browser["Next.js studio"]
  API["FastAPI /api/v1"]
  Engine["Mentor engine"]
  Domain["Domain policies"]
  Agents["Tutor, quiz, planner, research, coding, career"]
  Models["OpenAI, Anthropic, Gemini"]
  PG["PostgreSQL"]
  QD["Qdrant or local hash index"]

  Browser -->|REST| API
  API --> Engine
  Engine --> Domain
  Engine --> Agents
  Agents --> Models
  Engine --> PG
  Engine --> QD
```

With no model API key, the tutor still answers from the authored curriculum. With `QDRANT_URL` set to an HTTP address, embeddings go to Qdrant. Otherwise the API uses a deterministic local hash and stores the point id in Postgres.

Interactive API docs for a running process: [http://localhost:8000/docs](http://localhost:8000/docs).

## Tech Stack

| Layer | Choice |
| --- | --- |
| Studio | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Studio data | TanStack Query, Zustand |
| Auth | Clerk |
| API | FastAPI, Python 3.12, Pydantic v2, Uvicorn |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Vectors | Qdrant. Local hash index when Qdrant is unset |
| Models | OpenAI, Anthropic, Gemini |
| Payments | Stripe |
| Observability | OpenTelemetry, Langfuse |
| Studio hosting | Vercel |
| API hosting | One container image. Azure Container Apps is the primary host. AWS pulls the same image from GHCR |

## Local Setup

Install these before the project dependencies:

| Tool | Version |
| --- | --- |
| Python | 3.12 or newer |
| Node.js | 22 |
| npm | Comes with Node 22 |
| Docker Compose | Optional. Used by `make up` for PostgreSQL and Qdrant |
| Make | Optional. The commands below also work without it |

`make api` and `make test` expect a virtualenv at the repository root, named `.venv`.

Docker is optional. Without it, run the API against SQLite as shown in [Running Locally](#running-locally).

## Installation

From the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e "./backend[dev]"
cd frontend && npm ci && cd ..
```

`pip install -e "./backend[dev]"` installs the API and the development tools (`pytest`, `ruff`). `npm ci` installs the studio from `frontend/package-lock.json`.

## Configuration

The API reads environment variables and, when present, `backend/.env`. Create that file only for values you want to override. Empty optional values are treated as unset.

### API

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | `development`, `test`, or `production` |
| `DEV_AUTH` | on in development and test | Accept `X-Dev-User-Id`. Must be off in production |
| `DATABASE_URL` | `postgresql+psycopg://mentor:mentor@localhost:5432/mentor` | SQLAlchemy URL. SQLite is allowed outside production |
| `QDRANT_URL` | `memory` | `http://...` uses Qdrant. Any other value uses the local hash index |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated studio origins. Stripe return URLs must start with one of these |
| `CLERK_JWKS_URL` | unset | Required in production |
| `CLERK_ISSUER` | unset | Required in production |
| `CLERK_WEBHOOK_SECRET` | unset | Verifies `POST /api/v1/webhooks/clerk` |
| `OPENAI_API_KEY` | unset | Optional model provider |
| `ANTHROPIC_API_KEY` | unset | Optional model provider |
| `GEMINI_API_KEY` | unset | Optional model provider |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `ANTHROPIC_MODEL` | `claude-3-5-haiku-latest` | Anthropic chat model |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini chat model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Used when an OpenAI key is set |
| `STRIPE_SECRET_KEY` | unset | Checkout stays 503 while this is empty |
| `STRIPE_WEBHOOK_SECRET` | unset | Verifies `POST /api/v1/webhooks/stripe` |
| `STRIPE_PRICE_PRO` | unset | Price id for the Pro tier |
| `STRIPE_PRICE_RESEARCH` | unset | Price id for the Research tier |
| `LANGFUSE_PUBLIC_KEY` | unset | Both Langfuse keys are required before tracing is sent |
| `LANGFUSE_SECRET_KEY` | unset | |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | When set, spans go to the console exporter |
| `RATE_LIMIT_PER_MINUTE` | `60` | Per client IP |
| `AI_RATE_LIMIT_PER_MINUTE` | `20` | Tutor, quiz, lab, research, and the other AI prefixes |

Production startup fails if dev auth is on, Clerk is incomplete, `DATABASE_URL` is not PostgreSQL, or `QDRANT_URL` is not an HTTP URL.

### Studio

Copy `frontend/.env.example` to `frontend/.env.local`:

| Variable | Local value | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API origin |
| `NEXT_PUBLIC_DEV_AUTH` | `true` | Shows the Demo student, instructor, and admin switcher. Leave empty on a public deploy |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | empty locally | Required once Clerk protects the studio |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/sign-in` | |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/sign-up` | |

Do not commit `.env`, `.env.local`, or API keys.

## Running Locally

Two processes. In one terminal:

```bash
make api
```

`make api` listens on port 8000 and uses the default PostgreSQL URL. Start Postgres first, or point the API at SQLite:

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

On development startup the API creates tables and seeds the catalog. Learner progress is kept across restarts.

The session switcher is visible when `NEXT_PUBLIC_DEV_AUTH=true`. The API accepts `X-Dev-User-Id` in development and refuses it in production. A new dev user is always a student. The header cannot grant a role.

PostgreSQL and Qdrant together:

```bash
make up
```

That Compose file runs Postgres 16 (`mentor` / `mentor`, database `mentor`), Qdrant on port 6333, and the API on port 8000 with dev auth enabled. Do not publish that stack to the internet. Stop it with `make down`. The studio is still `make web`.

## Testing

Backend tests cover `backend/app/domain`. Coverage must stay at or above 90 percent.

```bash
make test
make lint
```

`make lint` runs Ruff check and a format check on `backend/app` and `backend/tests`.

Studio checks:

```bash
cd frontend
npm run typecheck
npm run build
```

GitHub Actions (`.github/workflows/ci.yml`) runs the same backend lint and tests, plus the studio typecheck and build, on push and pull request.

## Deployment

The studio deploys to Vercel. The API is one image, built from `backend/Dockerfile` (Python 3.12, non-root user `mentor`, `alembic upgrade head`, Uvicorn on `0.0.0.0:8000`).

`.github/workflows/publish.yml` pushes that image to GHCR on a `v*` tag or a manual run. It does not deploy on every push. Azure Container Apps is the primary API host. AWS ECS or App Runner can pull the same image.

Before a public studio deploy, set the Clerk publishable key, protect studio routes, and leave `NEXT_PUBLIC_DEV_AUTH` empty. Put secrets in the host secret store. Operator notes are in [docs/Deployment.md](docs/Deployment.md). The Azure layout, pipelines, backups, and recovery targets are in [docs/Infrastructure.md](docs/Infrastructure.md).

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
│   │   ├── repositories/
│   │   └── services/       # Mentor engine, model router, sandbox
│   ├── alembic/            # Schema migrations
│   ├── db/                 # Reference SQL
│   ├── tests/unit/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── app/                # Landing page and studio routes
│   ├── components/
│   ├── lib/
│   ├── stores/
│   └── Dockerfile
├── infrastructure/
│   └── compose.yaml        # Postgres, Qdrant, and the API
├── docs/                   # Architecture, API, OpenAPI, database, deployment
├── .github/workflows/      # CI and image publish
└── Makefile
```

Studio routes live under `frontend/app/(studio)/`: dashboard, tutor, quiz, paths, graph, flashcards, lab, research, and admin.

## Contribution Guidelines

Open a pull request against the main branch. Keep the change focused on one behavior.

- Put teaching decisions in `backend/app/domain`. Routes validate and delegate.
- Keep domain coverage at or above 90 percent. Run `make test` and `make lint` before you push.
- For studio changes, run `npm run typecheck` and `npm run build` in `frontend/`.
- If you add or change an HTTP route, update [docs/openapi.yaml](docs/openapi.yaml) and [docs/API.md](docs/API.md). Mark a route `live` only when the handler exists.
- Do not commit `.env` files, API keys, `dev.sqlite`, or `frontend/.next`.
- Ruff line length is 100. Follow [docs/Documentation-Standards.md](docs/Documentation-Standards.md) for docstrings, TypeDoc comments, and API notes.
- Describe the behavior a reviewer can verify. Screenshots help for studio layout changes.

CI must pass. A drop below the coverage gate fails the backend job.

## License

This repository does not include a `LICENSE` file. All rights are reserved. Do not copy or redistribute the code until the maintainers add a license.
