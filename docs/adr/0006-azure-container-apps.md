# ADR 0006 — Azure Container Apps for the API

- Status: Accepted (amended 2026-10-13)
- Date: 2026-10-13

## Context

The mentor is one container. It needs PostgreSQL, a private network, secrets, logs, and a path to more than one replica later. The studio is a Next.js application with a natural home on Vercel. The brief named Vercel, Azure, and AWS together.

## Problem

Choose a production host without building three backends.

## Decision

Vercel hosts the studio. Azure Container Apps in UK South hosts the API image (amended: West Europe, see below). The image is built from `backend/Dockerfile` and pushed to GHCR by `.github/workflows/publish.yml` on a `v*` tag or a manual run. CI on every push lints, tests, typechecks, and builds. CI does not deploy.

Azure Database for PostgreSQL Flexible Server is private. Key Vault holds secrets and the Container App reads them with a managed identity. Front Door is the public API edge once the replica count can exceed one. Qdrant Cloud sits in the same region. North Europe is the cold recovery region.

AWS ECS or App Runner may pull the same GHCR digest. That is an image pull, not a second implementation.

The full layout, environments, backup, and recovery targets are in `docs/Infrastructure.md`. Those Azure resources are specified. They are not provisioned by the current workflows.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Three bespoke cloud stacks | Divergent config, three sandbox policies, and three migration stories. |
| Azure App Service as the primary API | Works for a single web process. Container Apps matches the image, the migration job, and scale-to-zero in staging more directly. |
| Run the API on Vercel as Python functions | The lab forks a Python process for up to three seconds and ingestion holds a worker. A short-lived function is the wrong host. |
| Kubernetes now | The team would operate a cluster before it has a second service. Container Apps is the managed replica set. |

## Trade-off analysis

One image makes rollback “the previous digest.” The cost is Azure-specific networking and identity around that image. Those stay in the platform specification, not in application branches.

The container command runs `alembic upgrade head` and then Uvicorn. That is safe at one replica. Two replicas can migrate concurrently. Before the maximum replica count rises above one, migrations move to a Container Apps Job that finishes before traffic shifts.

The rate limiter is in-process: 60 requests per minute, 20 on AI routes. Two replicas double the allowance. Front Door becomes the shared limiter at the same moment.

Production stays between 1 and 4 replicas. The lab runs on the API replica, so the cap is a safety limit. Staging may scale to zero. Production stays at one replica overnight so webhooks and `/health` stay warm.

OpenTelemetry currently exports to the console when an endpoint is set. Availability monitoring until the OTLP exporter lands is the probe plus stdout.

## Consequences

- Production refuses dev auth, a non-Postgres URL, a missing Clerk issuer, and a non-HTTP Qdrant URL.
- Secrets are Key Vault references and Vercel environment variables. They are not baked into the image.
- A region outage restores Postgres in North Europe and starts the same digest. Vectors are rebuilt from chunk text.
- Publish does not deploy. Promotion is a reviewed step after a tag.

## Future considerations

- Add the GitHub Environment OIDC deploy described in `docs/Infrastructure.md`.
- Replace `ConsoleSpanExporter` with an OTLP exporter to Azure Monitor before the availability objective is treated as measured.
- Revisit the four-replica cap when the code runner leaves the API process.

## Amendment — 2026-10-13 hardening

- Migrations no longer run in the container command. The image only serves; `python -m app.cli migrate` runs as the `caj-mentor-migrate` Container Apps Job before each rollout, so replica count no longer constrains migrations.
- Rate limits are shared across replicas through Redis (`REDIS_URL`, required in production). Front Door's WAF rate rule is an outer layer only.
- Uvicorn trusts `X-Forwarded-For` only from `FORWARDED_ALLOW_IPS`, which must be set to the ingress range.
- `/health` is liveness only; `/ready` checks PostgreSQL, Qdrant, and Redis and is the readiness probe.
- OpenTelemetry exports over OTLP/HTTP when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
- The lab is off in production until the isolated runner exists, so it no longer runs on API replicas there.
- **Region.** The primary region is **West Europe**, not UK South, so that EU and UK learner data stays in the EU (SRS CON-002, CMP-007). North Europe remains the recovery region. Decided by the product owner on 2026-10-13. Qdrant Cloud, Redis, Key Vault, and Blob storage sit in the same region as the API.
