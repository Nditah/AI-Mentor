# AI Mentor — Operational Runbook

| Field | Value |
| --- | --- |
| Document ID | AIM-OPS-001 |
| Version | 1.0 |
| Date | 13 October 2026 |
| Owner | SRE / Production Operations |
| Applies to | Production (`APP_ENV=production`) and staging |
| Review cadence | Monthly, and after every SEV1/SEV2 postmortem |
| Related | [Deployment](Deployment.md), [Security](Security.md), [Architecture](Architecture.md), [Database](Database.md), [SRS](SRS.md) |

This runbook is written for the system as it runs today: one FastAPI container on Azure Container Apps, the Next.js studio on Vercel, Azure Database for PostgreSQL, optional Qdrant, Clerk, Stripe, and OpenAI/Anthropic/Gemini. Where a procedure depends on tooling that is not yet provisioned, it is marked **[TO PROVISION]**. Where it depends on a code change, it is marked **[CODE CHANGE]** with the reason.

---

## Contents

0. Quick reference, service inventory, known hazards
1. Incident Management
2. Escalation Procedures
3. Backup Procedures
4. Restore Procedures
5. Monitoring
6. Alert Thresholds
7. Troubleshooting Guides
8. Production Diagnostics
9. Service Health Checks
10. Performance Tuning
11. Recovery Procedures
12. Emergency Contacts Structure
- Appendix A — Standard release and rollback
- Appendix B — Communication templates
- Appendix C — Postmortem template

---

## 0. Quick reference

### 0.1 Shell variables used in this runbook

Set these once per session. Values live in the team password manager under "AI Mentor / Ops".

```bash
export RG="rg-aimentor-prod"                 # Azure resource group
export APP="ca-aimentor-api"                 # Container App name
export ENVNAME="cae-aimentor-prod"           # Container Apps environment
export PG="psql-aimentor-prod"               # PostgreSQL Flexible Server name
export PG_HOST="$PG.postgres.database.azure.com"
export WS="<log-analytics-workspace-guid>"   # Log Analytics workspace (customer) id
export KV="kv-aimentor-prod"                 # Key Vault
export API_URL="https://api.<domain>"        # Public API base
export WEB_URL="https://<domain>"            # Studio (Vercel)
export IMAGE="ghcr.io/<owner>/<repo>/api"    # Published by .github/workflows/publish.yml
export QDRANT_URL="https://<qdrant-host>:6333"
```

### 0.2 First five commands in any incident

```bash
# 1. Is the API answering, and in which mode?
curl -sS -m 5 -w '\nHTTP %{http_code} in %{time_total}s\n' "$API_URL/health"

# 2. Which revision is serving, how many replicas, is it healthy?
az containerapp revision list -n "$APP" -g "$RG" \
  --query "[].{rev:name,active:properties.active,traffic:properties.trafficWeight,replicas:properties.replicas,health:properties.healthState,created:properties.createdTime}" -o table

# 3. Live application logs
az containerapp logs show -n "$APP" -g "$RG" --type console --follow --tail 200

# 4. Platform events (crash loops, probe failures, OOM)
az containerapp logs show -n "$APP" -g "$RG" --type system --tail 100

# 5. Database reachable and not saturated
az postgres flexible-server show -g "$RG" -n "$PG" --query "{state:state,version:version,sku:sku.name,storageGB:storage.storageSizeGb}" -o table
```

A healthy `/health` response:

```json
{"status": "ok", "env": "production", "vector_store": "qdrant", "llm": "external"}
```

`llm: "curriculum"` in production means no model key is configured; the tutor is answering only from authored content. `/health` executes `select 1` against PostgreSQL and nothing else; it does **not** check Qdrant, Clerk, Stripe, or model providers.

### 0.3 Service inventory

| Component | Hosting | Role | State held | Owner |
| --- | --- | --- | --- | --- |
| Studio (Next.js 15) | Vercel | Learner and admin UI. `NEXT_PUBLIC_API_URL` is baked in at build time | None | Frontend lead |
| API (FastAPI, Python 3.12, Uvicorn) | Azure Container Apps, image from GHCR | All business logic, tutor, grading, lab, ingestion, webhooks | None (stateless) except in-process rate-limit counters | Backend lead |
| Code lab runner | Child `python -I` process inside the API container, 3 s timeout | Executes allowlisted learner Python | None | Backend lead + Security |
| PostgreSQL 16 | Azure Database for PostgreSQL Flexible Server | System of record: users, progress, XP, conversations, quizzes, documents, chunks | **All durable data** | Backend lead |
| Qdrant v1.13 | Managed or self-hosted | Vector store (configured; see hazard HZ-6) | Currently no application data | Backend lead |
| Clerk | SaaS | Identity, JWT (RS256 via JWKS), user webhooks | Identities | Backend lead |
| Stripe | SaaS | Checkout, subscriptions, webhooks | Billing | Backend lead + Finance |
| OpenAI / Anthropic / Gemini | SaaS | Completions; OpenAI also embeddings | None | AI lead |
| Langfuse | SaaS | LLM traces (best-effort; see HZ-8) | Traces | AI lead |
| GHCR | GitHub | Image registry, tags `v*` | Images | Backend lead |
| GitHub Actions | GitHub | `ci` on push/PR, `publish` on tag | — | Backend lead |

### 0.4 Request path

```text
Browser -> Vercel (studio) -> HTTPS -> Container Apps ingress (Envoy) -> Uvicorn -> FastAPI
  -> RateLimitMiddleware (per process, keyed by client host)
  -> current_user(): Clerk JWT verified via JWKS -> upsert_user() in PostgreSQL
  -> MentorEngine -> domain policies -> ProviderRouter (OpenAI -> Anthropic -> Gemini -> curriculum fallback)
  -> PostgreSQL (SQLAlchemy pool, pre-ping)
```

Routes are synchronous `def` functions. FastAPI runs them in a thread pool (AnyIO default: 40 threads per worker process). Anything that blocks a thread — a slow model call, a slow embedding call, a lab run, a slow query — consumes that pool.

### 0.5 Known operational hazards (read before your first on-call shift)

These are properties of the current build that cause or worsen incidents. Each has a troubleshooting guide and a tracked fix.

| ID | Hazard | Effect in production | Guide | Permanent fix |
| --- | --- | --- | --- | --- |
| HZ-1 | Model SDK clients are created without an explicit timeout (SDK default is minutes, with automatic retries) | A slow or hung provider holds threads for minutes; the thread pool fills; **every** route, including `/health`, stalls | TG-03 | **[CODE CHANGE]** set `timeout≈20s`, `max_retries≤1` on OpenAI/Anthropic/Gemini clients |
| HZ-2 | Rate limiter keys on `request.client.host`; Uvicorn trusts `X-Forwarded-For` only from `127.0.0.1` by default | Behind Container Apps ingress, many users may share one key; legitimate users get `429` | TG-02 | Set `FORWARDED_ALLOW_IPS` (env, read by Uvicorn) and move to a shared limiter |
| HZ-3 | Rate limiter is per process | Effective limit = configured limit × workers × replicas | TG-02 | Shared limiter (Redis or edge) |
| HZ-4 | Container start runs `alembic upgrade head`, then the lifespan seeds the catalog — on **every** replica and worker | Concurrent migrations or seed upserts at scale-out or deploy can fail and crash-loop replicas | TG-07 | Run migrations as a one-off Container Apps Job before shifting traffic |
| HZ-5 | Research analysis re-embeds every chunk of the document at query time | With an OpenAI key, one embeddings API call per chunk per question; large documents take minutes and cost money | TG-08 | **[CODE CHANGE]** persist vectors (Qdrant) and query them |
| HZ-6 | No code path writes to or reads from Qdrant yet; `embeddings.qdrant_point_id` is recorded but no point is stored | Qdrant outages have no learner impact today; Qdrant backups currently protect nothing | §3.4 | Implement Qdrant writes (SRS RAG-011) |
| HZ-7 | `/health` checks only PostgreSQL | A green health check does not mean tutor, auth, or billing work | §9 | Add `/ready` with dependency checks |
| HZ-8 | Langfuse tracing calls `client.trace(...)`, which is not present in current Langfuse SDK major versions; the code silently returns | Do not rely on Langfuse for incident evidence until verified | §5.3 | **[CODE CHANGE]** migrate to current SDK API |
| HZ-9 | OpenTelemetry exports spans to the console, not OTLP | Spans appear as log lines (noisy, not queryable as traces) | §5.3 | Configure an OTLP exporter |
| HZ-10 | Clerk JWKS client is created without a timeout; JWKS fetch errors are not converted to 401 | Clerk/JWKS outage after the key cache expires → slow `500`s on every authenticated request | TG-05 | **[CODE CHANGE]** timeout, catch `PyJWKClientError`, longer cache |
| HZ-11 | Every authenticated request calls `upsert_user()` | One write per request; adds DB load and lock contention under burst | §10.4 | Upsert only on first sight or claim change |
| HZ-12 | Learner code runs in a child interpreter inside the API container, not an isolated sandbox | A policy bypass would execute inside the API container's trust boundary | TG-17 | gVisor/microVM runner (Roadmap item 3) |
| HZ-13 | Ingestion is synchronous in the request | Large uploads hold a thread and a DB transaction for the whole parse + embed | TG-08 | Job queue (Roadmap item 4) |
| HZ-14 | Clerk `user.deleted` is not handled | Deleted Clerk users keep local records; erasure requests are manual | §11.9 | Handle `user.deleted` |

---

## 1. Incident Management

### 1.1 What counts as an incident

Declare an incident when any of the following is true, or when in doubt:

- An alert at **critical** level fires (§6).
- Learners cannot sign in, chat, take quizzes, run lab code, or pay.
- Any learner can see another learner's data, or any secret may have been exposed.
- A model produces harmful content that reached learners.
- A vendor (Azure, Vercel, Clerk, Stripe, model provider) declares an outage affecting us.
- A deploy or migration fails in production.

Declaring an incident that turns out to be minor costs nothing. Not declaring a real one costs time.

### 1.2 Severity levels

| Severity | Definition | AI Mentor examples | Ack | Update cadence | Who is paged |
| --- | --- | --- | --- | --- | --- |
| **SEV1 — Critical** | Platform unusable for most learners, or data/security breach, or legal exposure | API `5xx` > 25% for 5 min; `/health` down on all replicas; any cross-learner data exposure; sandbox escape; secret leaked publicly; database lost or corrupted; mass incorrect billing | 5 min | 30 min | On-call primary + secondary, Incident Commander, Engineering lead, Security (if data/security) |
| **SEV2 — Major** | A core journey is broken or badly degraded for many learners; no data loss | All model providers failing (tutor in curriculum fallback); sign-in failing for a subset; Stripe webhooks failing (subscriptions not activating); research upload broken; p95 latency > 3× normal for 15 min; Vercel studio down | 15 min | 60 min | On-call primary, component owner |
| **SEV3 — Minor** | One feature degraded, workaround exists, limited learners | One model provider down (failover working); leaderboard wrong; lab timeouts for one project; elevated `429`s for some users | 4 business hours | Daily | On-call primary (business hours) |
| **SEV4 — Low** | Cosmetic or internal-only | Admin analytics slow; log noise; a typo in a lesson | Next sprint | — | Ticket only |

Upgrade severity as soon as impact grows. Downgrade only when the IC agrees.

### 1.3 Incident roles

| Role | Responsibility | Default holder |
| --- | --- | --- |
| **Incident Commander (IC)** | Owns the incident. Sets severity, assigns roles, decides on mitigations (rollback, kill switches), declares resolution. Does not debug. | On-call secondary or Engineering lead for SEV1 |
| **Operations Lead (Ops)** | Hands on keyboard. Runs diagnostics and mitigations. Narrates actions in the incident channel before running them. | On-call primary |
| **Communications Lead** | Status page, learner-facing messages, internal updates, vendor tickets. | PM or Support lead |
| **Scribe** | Timeline with UTC timestamps of observations, decisions, and commands. | Anyone not in another role |
| **Subject-matter expert** | Pulled in by IC: AI lead (model behaviour), Security lead (breach), Finance (billing). | As needed |

For SEV3/SEV4 one person may hold all roles.

### 1.4 Incident lifecycle

```text
Detect -> Triage (5 min) -> Declare -> Mitigate -> Monitor -> Resolve -> Postmortem -> Follow-ups
```

**Step 1 — Detect.** Sources: alerts (§6), synthetic probes, learner reports via support, vendor status pages, team members.

**Step 2 — Triage (target: 5 minutes).**

1. Acknowledge the page.
2. Run the five commands in §0.2.
3. Answer: What is broken? For whom? Since when? What changed recently (deploy, config, secret, vendor)?
4. Check recent changes:
   ```bash
   az containerapp revision list -n "$APP" -g "$RG" --query "sort_by([], &properties.createdTime)[-3:].{rev:name,created:properties.createdTime,image:properties.template.containers[0].image}" -o table
   gh run list --workflow publish --limit 5
   ```
5. Check vendor status pages (§12.3).
6. Assign severity using §1.2.

**Step 3 — Declare.**

1. Create channel `#inc-YYYYMMDD-<short-name>` in the team chat.
2. Post the declaration (Appendix B.1).
3. Assign IC, Ops, Comms, Scribe.
4. SEV1/SEV2: start a video bridge and pin the link.
5. SEV1/SEV2 with learner impact > 15 minutes: Comms posts to the status page (Appendix B.2).

**Step 4 — Mitigate. Prefer reversible, fast actions over root-causing.** In order of preference:

| Mitigation | When | Procedure |
| --- | --- | --- |
| Roll back to the previous revision | Anything that started after a deploy | §11.1 |
| Disable a failing model provider | One provider slow or erroring | §11.4 (remove its key secret, new revision) |
| Scale out | CPU/thread saturation without a code defect | §10.2 |
| Restart replicas | Thread pool exhausted, memory leak | §11.2 |
| Fail over to a restored database | Database corruption or loss | §4 / §11.6 |
| Block abusive traffic | Abuse or scraping | §7 TG-16 |
| Rotate a secret | Suspected exposure | §11.8 |

Ops states every command in the channel **before** running it. IC approves anything destructive (deleting data, restoring over a live database, rotating identity secrets).

**Step 5 — Monitor.** After mitigation, watch the relevant signals for at least 15 minutes (SEV1: 30 minutes) before declaring resolved.

**Step 6 — Resolve.** IC declares resolution when user impact has ended and no mitigation is at risk of reverting. Comms posts the resolution update. Scribe freezes the timeline.

**Step 7 — Postmortem.** Required for every SEV1 and SEV2, optional for SEV3. Draft within 2 business days, review meeting within 5 business days, blameless (Appendix C). Every action item has an owner and a due date and is tracked in the backlog with label `postmortem`.

### 1.5 Security and data-protection incidents

Use this branch when there is any suspicion of: unauthorised access to learner data, cross-learner exposure, credential or secret leakage, sandbox escape, malicious upload, or account takeover.

1. Declare at least SEV2; SEV1 if learner personal data may be exposed.
2. Page the **Security lead** immediately. The Security lead becomes co-IC.
3. **Preserve evidence before changing anything that destroys it**: export relevant logs (§8.2), note revision names and image digests, snapshot the database if data tampering is suspected (§3.2 on-demand backup).
4. Contain: revoke or rotate exposed secrets (§11.8), disable the affected route or feature, suspend affected accounts.
5. Start the **72-hour regulatory clock** from the moment the team becomes aware of a personal-data breach. The DPO/Legal contact (§12) decides whether to notify the supervisory authority (GDPR Art. 33, UK ICO, Nigeria NDPC) and affected learners.
6. Do not discuss details in public channels or with learners until Legal approves wording.
7. Postmortem is mandatory and includes a data-impact assessment: which records, which learners, which period.

### 1.6 Harmful AI output incidents

When a learner reports, or monitoring finds, harmful, unsafe, or seriously wrong tutor output:

1. SEV3 by default; SEV2 if harmful content (self-harm, violence, sexual, harassment) reached a learner or if the issue is systematic.
2. Collect: conversation id, message id, timestamp, prompt version, provider. Query in §8.4.
3. Reproduce in staging with the same inputs.
4. Mitigate: if one provider is responsible, disable it (§11.4). If a prompt change is responsible, roll back the revision (§11.1). If a lesson/catalog entry is responsible, hotfix the content.
5. If self-harm intent was expressed by a learner, notify the Trust & Safety owner the same day.

---

## 2. Escalation Procedures

### 2.1 Time-based escalation

| Elapsed since page | SEV1 | SEV2 | SEV3 |
| --- | --- | --- | --- |
| 0 min | Primary on-call paged | Primary on-call paged | Ticket + chat notification |
| 5 min, no ack | Secondary on-call paged automatically | — | — |
| 10 min, no ack | Engineering lead phoned | Secondary paged | — |
| 15 min | IC assigned; status page posted if learner-facing | Primary ack required | — |
| 30 min, not mitigated | Engineering lead joins; vendor support opened at highest severity | IC assigned | — |
| 60 min, not mitigated | CTO/Head of Engineering informed; consider DR (§11.7) | Engineering lead informed | — |
| 4 h, not mitigated | Executive update; customer-facing statement reviewed by Legal/PM | Vendor escalation | Primary escalates to component owner |

### 2.2 Functional escalation (who to pull in)

| Symptom area | First escalation | Second escalation |
| --- | --- | --- |
| API errors, latency, deploys, containers | Backend lead | Engineering lead |
| Database (connections, locks, storage, restore) | Backend lead | Azure Support (Severity A for SEV1) |
| Model output quality, provider outages, cost | AI lead | Provider support |
| Sign-in, JWT, roles | Backend lead | Clerk support |
| Payments, subscriptions | Backend lead + Finance | Stripe support |
| Studio UI, Vercel | Frontend lead | Vercel support |
| Sandbox, data exposure, secrets, abuse | Security lead | External incident response retainer |
| Learner communications, status page | PM / Support lead | Head of Product |
| Regulatory notification | DPO / Legal | External counsel |

### 2.3 Vendor escalation

Open vendor tickets from the account that owns the contract (credentials in the password manager). Always include: our account/tenant id, UTC start time, affected resource ids, request ids or trace ids, impact statement, and what we have already tried.

| Vendor | Open a ticket | Severity to request |
| --- | --- | --- |
| Microsoft Azure | Azure Portal → Help + support → Create a support request (or `az support tickets create`) | SEV1: Severity A (24×7, requires Professional Direct or higher plan); SEV2: Severity B |
| Vercel | Dashboard → Help, or support email on plan | Highest available on plan |
| Clerk | Dashboard → Support | Urgent |
| Stripe | Dashboard → Support → Contact | Urgent (payments down) |
| OpenAI / Anthropic / Google | Platform console support / account manager | Highest available; usually rely on failover (§11.4) instead |
| GitHub (GHCR/Actions) | support.github.com | Only if deploys blocked |

### 2.4 Escalation rules

- Escalating is never a failure. Escalate when you are stuck for 15 minutes, when you need approval for a destructive action, or when the incident crosses a functional boundary.
- When you escalate, state: severity, impact, what you've ruled out, what you need from the person.
- Hand-offs (shift change, fatigue) are explicit: "I am handing Ops to <name> at <UTC>; current state is …". Nobody works a SEV1 for more than 4 hours without a break; the IC enforces this.

---

## 3. Backup Procedures

### 3.1 What needs protecting

| Asset | Where | Durable data? | Protection | RPO | RTO |
| --- | --- | --- | --- | --- | --- |
| PostgreSQL database `mentor` | Azure PG Flexible Server | **Yes — the only system of record** | Automated PITR backups (35-day retention), on-demand backups before risky changes, nightly logical dump to separate storage | ≤ 15 min (PITR); ≤ 24 h (logical) | ≤ 4 h |
| Qdrant collections | Qdrant | Not today (HZ-6). When implemented: derived from PostgreSQL chunks | Snapshots (§3.4); rebuildable | Rebuildable | ≤ 12 h (re-embed) |
| Uploaded originals | Not stored; parsed in memory, only chunks kept in PostgreSQL | No | Covered by PostgreSQL | — | — |
| Container images | GHCR, tag `v*` | Yes (deploy artefacts) | Tags are never overwritten or deleted for released versions | — | Minutes |
| Source and catalog (`backend/app/domain/catalog.py`) | Git | Yes | Git remote + mirror | — | Minutes |
| Configuration and secrets | Container Apps secrets, Vercel env, Key Vault | Yes | Key Vault (soft delete + purge protection) holds the canonical copy; Container Apps and Vercel reference it | — | ≤ 30 min |
| Identities | Clerk | Vendor-managed | Weekly user export via Clerk Backend API for reconciliation | 7 days (reconciliation only) | Vendor |
| Billing | Stripe | Vendor-managed; Stripe is source of truth | Local `subscription_status` reconstructable from Stripe | — | Hours (re-sync) |
| Log Analytics | Azure | Diagnostic only | Retention 30 days hot, 90 days archive | — | — |

### 3.2 PostgreSQL — automated backups (verify, do not assume)

Azure Database for PostgreSQL Flexible Server takes automated full snapshots and continuously archives WAL, enabling point-in-time restore anywhere in the retention window.

**Required configuration (check monthly, §9.4):**

```bash
az postgres flexible-server show -g "$RG" -n "$PG" \
  --query "{retentionDays:backup.backupRetentionDays, geoRedundant:backup.geoRedundantBackup, earliestRestore:backup.earliestRestoreDate, ha:highAvailability.mode}" -o table
```

Expected: `retentionDays = 35`, `geoRedundant = Enabled`, `ha = ZoneRedundant` (or `SameZone` if the region lacks zones).

If retention is lower:

```bash
az postgres flexible-server update -g "$RG" -n "$PG" --backup-retention 35
```

Geo-redundant backup can only be chosen when the server is created. If it is `Disabled`, the logical dump in §3.3 is the only off-region copy; raise a ticket to recreate the server with geo-redundancy during a maintenance window.

**On-demand backup — mandatory before:** any Alembic migration in production, bulk data fixes, role/permission changes run as SQL, and vendor-requested maintenance.

```bash
STAMP=$(date -u +%Y%m%dT%H%MZ)
az postgres flexible-server backup create -g "$RG" -n "$PG" --backup-name "pre-change-$STAMP"
az postgres flexible-server backup list -g "$RG" -n "$PG" -o table
```

Record the backup name and the exact UTC time in the change ticket. The UTC time is also your PITR target if the change goes wrong.

### 3.3 PostgreSQL — nightly logical dump **[TO PROVISION]**

Purpose: an independent copy outside the PostgreSQL service (protects against server deletion, ransomware in the subscription, or a backup-service fault), and the easiest source for single-table recovery.

Run as a scheduled Container Apps Job at 02:30 UTC using a `postgres:16` image and a read-only role:

```bash
# Inside the job container
set -euo pipefail
STAMP=$(date -u +%Y%m%dT%H%MZ)
pg_dump "host=$PG_HOST port=5432 dbname=mentor user=backup_ro sslmode=require" \
  --format=custom --compress=9 --no-owner --no-privileges \
  --file="/tmp/mentor-$STAMP.dump"
pg_restore --list "/tmp/mentor-$STAMP.dump" > /dev/null   # integrity check: archive is readable
az storage blob upload --auth-mode login \
  --account-name "$BACKUP_SA" --container-name pg-logical \
  --name "mentor-$STAMP.dump" --file "/tmp/mentor-$STAMP.dump" --tier Cool
```

Storage requirements for `$BACKUP_SA`:
- In a **different region** from the database (for example North Europe if primary is West Europe).
- Container `pg-logical` with an **immutability policy** (time-based retention 35 days) and soft delete 14 days.
- Lifecycle rule: delete blobs older than 35 days (keep the first dump of each month for 12 months).
- Access by managed identity only; no account keys distributed.

Create the read-only role once:

```sql
CREATE ROLE backup_ro LOGIN PASSWORD '<from Key Vault>';
GRANT CONNECT ON DATABASE mentor TO backup_ro;
GRANT USAGE ON SCHEMA public TO backup_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_ro;
```

Alert if no new blob appears in `pg-logical` for 26 hours (§6).

### 3.4 Qdrant snapshots

Today no learner-facing data lives in Qdrant (HZ-6), so snapshots are not required for recovery. Once Qdrant writes are implemented, run daily at 03:00 UTC for each collection:

```bash
for c in $(curl -sS -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections" | jq -r '.result.collections[].name'); do
  curl -sS -X POST -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections/$c/snapshots?wait=true" | jq .
done
# List snapshots of one collection
curl -sS -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections/<name>/snapshots" | jq .
```

Download snapshots to the backup storage account and keep 7 daily copies. PostgreSQL remains the source of truth: chunk text is in `document_chunks`, so a collection can always be rebuilt by re-embedding (§4.6).

### 3.5 Secrets and configuration backup

- Key Vault must have **soft delete (90 days)** and **purge protection** enabled:
  ```bash
  az keyvault show -n "$KV" --query "{softDelete:properties.enableSoftDelete, purgeProtection:properties.enablePurgeProtection, retention:properties.softDeleteRetentionInDays}" -o table
  ```
- Container Apps environment variables and secret *names* are exported weekly to the ops repository (values excluded):
  ```bash
  az containerapp show -n "$APP" -g "$RG" --query "properties.template.containers[0].env[].{name:name,secretRef:secretRef}" -o json > ops/config/containerapp-env.json
  az containerapp secret list -n "$APP" -g "$RG" --query "[].name" -o json > ops/config/containerapp-secret-names.json
  ```
- Vercel environment variable names: `vercel env ls production` exported weekly.

### 3.6 Identity reconciliation export (Clerk)

Weekly job: page through the Clerk Backend API `GET /v1/users` and store `id, primary email, created_at, public_metadata.role` as JSON in the backup storage account (35-day retention). Used only to reconcile local `users.clerk_id` after a database restore and to detect orphaned accounts.

### 3.7 Backup schedule summary

| Time (UTC) | Job | Retention | Alert if missing |
| --- | --- | --- | --- |
| Continuous | PostgreSQL WAL archiving (Azure) | 35 days | Azure backup failure event |
| Daily (Azure-managed) | PostgreSQL automated snapshot | 35 days | `earliestRestoreDate` older than 36 days or newer than 34 days |
| 02:30 daily | Logical `pg_dump` to cross-region immutable blob | 35 days + monthly 12 months | No blob for 26 h |
| 03:00 daily | Qdrant snapshots (once Qdrant holds data) | 7 days | No snapshot for 26 h |
| Before every migration/bulk change | On-demand PostgreSQL backup | Until next monthly review | Change ticket checklist |
| Sunday 04:00 | Config/secret-name export; Clerk user export | 35 days | No commit/blob for 8 days |

### 3.8 Backup verification

| Check | Frequency | Procedure | Pass criteria |
| --- | --- | --- | --- |
| Logical dump readable | Daily (in job) | `pg_restore --list` | Exit code 0 |
| Logical dump restorable | Weekly | Restore latest dump into a scratch database (§4.4) and run §4.7 validation queries | Row counts within 1% of production at dump time |
| PITR restorable | Quarterly (restore drill) | Full PITR to a new server (§4.2), point a staging API at it, run smoke test (§9.6) | RTO ≤ 4 h, RPO ≤ 15 min measured |
| Qdrant snapshot restorable | Quarterly, once in use | Recover into a scratch collection (§4.6) | Point counts match |

Record every drill result in `ops/drills/YYYY-MM-DD.md` with timings.

---

## 4. Restore Procedures

**Golden rule: never restore over the live production server.** Restore to a *new* server, validate, then cut over by changing `DATABASE_URL`. The old server stays untouched until the incident is closed, so you can always go back.

### 4.1 Choose the restore path

| Situation | Path | Data loss |
| --- | --- | --- |
| Bad migration, bad bulk update, accidental `DELETE`/`DROP` affecting much of the database | §4.2 PITR to just before the change | Writes after the target time (reconcile with §4.8) |
| A few rows or one table damaged; rest of DB is fine | §4.3 restore side-by-side and copy the rows back | None |
| Primary region unavailable | §4.5 geo-restore | Up to ~1 h (geo-backup lag) |
| Server deleted or backups unusable | §4.4 restore logical dump | Up to 24 h |
| Qdrant collection lost or corrupted | §4.6 | None (rebuild from PostgreSQL) |

### 4.2 Point-in-time restore (PITR) to a new server

1. **Freeze writes** to stop the damage spreading and to bound reconciliation. Pick one:
   - Preferred: put the studio into maintenance mode (Vercel env `NEXT_PUBLIC_MAINTENANCE=true` + redeploy) **[TO PROVISION]**, and scale the API to zero:
     ```bash
     az containerapp update -n "$APP" -g "$RG" --min-replicas 0 --max-replicas 0
     ```
   - If you cannot take downtime: leave the API up and accept that writes after the restore point must be reconciled (§4.8).
2. **Pick the restore time.** Find the exact UTC time of the bad change: change ticket, Alembic logs, or `az containerapp logs`. Choose 1–2 minutes earlier. Times must be ISO 8601 UTC.
3. **Restore:**
   ```bash
   RESTORE_TIME="2026-10-13T10:14:00Z"
   NEW_PG="$PG-r$(date -u +%m%d%H%M)"
   az postgres flexible-server restore -g "$RG" --name "$NEW_PG" \
     --source-server "$PG" --restore-time "$RESTORE_TIME"
   ```
   Typical duration: 15–60 minutes depending on size and WAL to replay. Monitor with `az postgres flexible-server show -g "$RG" -n "$NEW_PG" --query state`.
4. **Re-apply server configuration that is not copied by restore:** firewall rules / private endpoint / VNet integration, server parameters you changed (§10.3), Entra ID admins, HA settings.
   ```bash
   az postgres flexible-server parameter list -g "$RG" -s "$PG" --query "[?source=='user-override'].{name:name,value:value}" -o table
   # re-apply each on $NEW_PG with: az postgres flexible-server parameter set -g "$RG" -s "$NEW_PG" --name <n> --value <v>
   ```
5. **Validate** the restored server (§4.7). Do not proceed until all checks pass.
6. **Cut over:**
   ```bash
   NEW_URL="postgresql+psycopg://<user>:<password>@$NEW_PG.postgres.database.azure.com:5432/mentor?sslmode=require"
   az keyvault secret set --vault-name "$KV" --name database-url --value "$NEW_URL"
   az containerapp secret set -n "$APP" -g "$RG" --secrets "database-url=$NEW_URL"
   az containerapp update -n "$APP" -g "$RG" --min-replicas 2 --max-replicas 10 \
     --revision-suffix "restore$(date -u +%H%M)"
   ```
   Container Apps does not restart running revisions when a secret changes; the `update` with a new revision suffix forces new replicas that read the new value. On start, `alembic upgrade head` runs; on a restored database at the same schema this is a no-op.
7. **Run the smoke test** (§9.6) and watch error rates for 30 minutes.
8. **Reconcile** writes lost between the restore point and the freeze (§4.8).
9. **Lift maintenance mode.**
10. Keep the old server for at least 7 days (stopped, to save cost: `az postgres flexible-server stop -g "$RG" -n "$PG"`). Delete only after the postmortem confirms it is not needed; take a final on-demand backup first.

### 4.3 Recover specific rows or tables without a full cutover

1. PITR to a side server as in §4.2 steps 2–3 (no write freeze needed).
2. Export the affected rows from the side server and import them into production inside a transaction. Example: restoring one learner's deleted flashcards.
   ```bash
   # On the side server: export
   psql "host=$NEW_PG.postgres.database.azure.com dbname=mentor user=<admin> sslmode=require" -c \
     "\copy (SELECT * FROM flashcards WHERE user_id = '<uuid>') TO 'flashcards.csv' CSV HEADER"
   psql "host=$NEW_PG.postgres.database.azure.com dbname=mentor user=<admin> sslmode=require" -c \
     "\copy (SELECT r.* FROM reviews r JOIN flashcards f ON f.id = r.flashcard_id WHERE f.user_id = '<uuid>') TO 'reviews.csv' CSV HEADER"
   ```
   ```sql
   -- On production
   BEGIN;
   CREATE TEMP TABLE flashcards_restore (LIKE flashcards INCLUDING ALL);
   \copy flashcards_restore FROM 'flashcards.csv' CSV HEADER
   INSERT INTO flashcards SELECT * FROM flashcards_restore ON CONFLICT (id) DO NOTHING;
   CREATE TEMP TABLE reviews_restore (LIKE reviews INCLUDING ALL);
   \copy reviews_restore FROM 'reviews.csv' CSV HEADER
   INSERT INTO reviews SELECT * FROM reviews_restore ON CONFLICT (id) DO NOTHING;
   -- verify counts, then
   COMMIT;
   ```
3. Respect foreign-key order: parents first (`users` → `conversations` → `messages`; `quizzes` → `questions` → `quiz_results`; `research_documents` → `document_chunks` → `embeddings`; `flashcards` → `reviews`).
4. If the user's XP is affected, recompute `users.xp` from `xp_events` (§8.4 reconciliation query) and `users.level = 1 + xp / 250`.
5. Delete the side server when done.

### 4.4 Restore from the nightly logical dump

```bash
# 1. Download the dump you need
az storage blob download --auth-mode login --account-name "$BACKUP_SA" \
  --container-name pg-logical --name "mentor-<STAMP>.dump" --file mentor.dump

# 2. Create a fresh server (or use the scratch server for weekly verification)
az postgres flexible-server create -g "$RG" -n "$NEW_PG" --version 16 \
  --tier GeneralPurpose --sku-name Standard_D2ds_v5 --storage-size 128 \
  --high-availability Disabled --backup-retention 35 --public-access None
az postgres flexible-server db create -g "$RG" -s "$NEW_PG" -d mentor

# 3. Restore (parallel jobs speed this up)
pg_restore --dbname="host=$NEW_PG.postgres.database.azure.com dbname=mentor user=<admin> sslmode=require" \
  --no-owner --no-privileges --jobs=4 --exit-on-error mentor.dump

# 4. Confirm schema version matches the image you will run
psql "host=$NEW_PG.postgres.database.azure.com dbname=mentor user=<admin> sslmode=require" -c "SELECT version_num FROM alembic_version;"
```

Then validate (§4.7) and cut over (§4.2 step 6). Recreate the application role and grants, since `--no-owner --no-privileges` drops them.

### 4.5 Geo-restore (primary region down)

Requires geo-redundant backups (§3.2).

```bash
PG_ID=$(az postgres flexible-server show -g "$RG" -n "$PG" --query id -o tsv)
az postgres flexible-server geo-restore -g "$RG-dr" --name "$PG-dr" \
  --source-server "$PG_ID" --location northeurope
```

Continue with §11.7 (regional disaster recovery), which also moves the API.

### 4.6 Qdrant restore or rebuild

**From snapshot** (once Qdrant holds data):

```bash
curl -sS -X PUT -H "api-key: $QDRANT_API_KEY" -H 'Content-Type: application/json' \
  "$QDRANT_URL/collections/<name>/snapshots/recover" \
  -d '{"location": "<https-url-or-file:///qdrant/snapshots/...>", "priority": "snapshot"}'
curl -sS -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections/<name>" | jq '.result.points_count'
```

**Rebuild from PostgreSQL** (always possible): every `document_chunks` row has its text; `embeddings` records the model used. Re-embed all chunks with the configured model and upsert with `id = embeddings.qdrant_point_id` and payload `{document_id, user_id(owner), chunk_id, ordinal}`. Run in batches of 100 chunks and throttle to the embedding provider's rate limit. Estimated cost and duration must be computed before starting:

```sql
SELECT count(*) AS chunks, sum(length(text)) / 4 AS approx_tokens FROM document_chunks;
```

### 4.7 Post-restore validation checklist

Run against the restored server before cutover. Compare with the same queries on production (if reachable) or with the last known values in the daily health report.

```sql
-- Schema version must match the image's Alembic head
SELECT version_num FROM alembic_version;

-- Row counts for core tables
SELECT 'users' t, count(*) FROM users UNION ALL
SELECT 'conversations', count(*) FROM conversations UNION ALL
SELECT 'messages', count(*) FROM messages UNION ALL
SELECT 'quiz_results', count(*) FROM quiz_results UNION ALL
SELECT 'progress', count(*) FROM progress UNION ALL
SELECT 'xp_events', count(*) FROM xp_events UNION ALL
SELECT 'flashcards', count(*) FROM flashcards UNION ALL
SELECT 'research_documents', count(*) FROM research_documents UNION ALL
SELECT 'document_chunks', count(*) FROM document_chunks;

-- Latest write time should be just before the restore point
SELECT max(created_at) FROM xp_events;
SELECT max(created_at) FROM messages;

-- At least one admin exists (the API refuses to remove the last admin, but restores can predate role changes)
SELECT count(*) FROM users WHERE role = 'admin';

-- XP integrity: users whose xp differs from their events
SELECT u.id, u.xp, coalesce(sum(e.amount),0) AS events_xp
FROM users u LEFT JOIN xp_events e ON e.user_id = u.id
GROUP BY u.id, u.xp HAVING u.xp <> coalesce(sum(e.amount),0) LIMIT 20;

-- Catalog present (seed also re-upserts on API start)
SELECT count(*) FROM learning_paths; SELECT count(*) FROM lessons; SELECT count(*) FROM concepts;
```

Pass criteria: Alembic version equals the deployed image's head; counts plausible (no table unexpectedly empty); latest timestamps match the restore target; ≥ 1 admin; XP mismatches explained.

### 4.8 Reconciling writes lost after the restore point

Data written between the restore point and the freeze is not in the restored database.

| Data | Reconciliation |
| --- | --- |
| New users | Re-created automatically on their next request (JWT → `upsert_user`). Optionally replay Clerk `user.created` webhooks from the Clerk dashboard for the window. |
| Subscriptions | Replay Stripe events for the window: Stripe Dashboard → Developers → Events → filter by time → Resend to endpoint, or `stripe events resend <evt_id>`. Then verify with §8.4 subscription query. |
| XP, progress, quizzes, messages | Lost for the window. If the old server still holds them (bad change was limited), copy rows created after `RESTORE_TIME` from the old server using §4.3, excluding the damaged rows. Otherwise inform affected learners. |
| Research uploads | Lost for the window; learners re-upload. Comms sends a notice to users with `research_documents.created_at` in the window on the old server. |

---

## 5. Monitoring

### 5.1 Service level objectives

| SLO | Indicator | Target | Window | Error budget |
| --- | --- | --- | --- | --- |
| API availability | Synthetic `GET /health` success and non-`5xx` share of real requests (excluding `429`) | 99.5% | 30 days rolling | 3 h 36 min |
| Tutor latency | `POST /api/v1/chat` duration p95 | ≤ 8 s (non-streaming today); ≤ 1.5 s time to first token once streaming ships | 7 days | 5% of requests |
| Read latency | `GET /api/v1/dashboard`, `/progress`, `/learning-paths` p95 | ≤ 500 ms | 7 days | 5% |
| Lab run | `POST /api/v1/lab/run` p95 | ≤ 5 s | 7 days | 5% |
| Sign-in success | Share of authenticated requests not returning `401` due to JWKS errors | 99.9% | 30 days | — |
| Payment activation | Stripe webhooks processed `2xx` | 99.9% | 30 days | — |

**Error budget policy:** when more than 50% of the monthly budget is used, non-urgent deploys require IC/Engineering lead approval; at 100%, feature deploys freeze until the budget recovers or a reliability fix ships.

### 5.2 What to watch (golden signals per component)

| Component | Traffic | Errors | Latency | Saturation |
| --- | --- | --- | --- | --- |
| API | Requests/min by route | `5xx` rate, `429` rate, `401` rate, tracebacks in logs | p50/p95/p99 by route (from access logs or ingress) | CPU %, memory %, replica count, restarts, thread-pool saturation (proxy: requests in flight / 40 per worker) |
| PostgreSQL | Transactions/s | `connections_failed`, deadlocks | Query duration (pg_stat_statements) | `cpu_percent`, `memory_percent`, `storage_percent`, `active_connections` vs `max_connections`, `maximum_used_transactionIDs` |
| Model providers | Calls/min by provider | `model provider <x> failed` log lines, fallback-to-curriculum rate | Call duration | Provider rate-limit (`429`) responses, daily spend |
| Lab runner | Runs/min | `rejected`, `timeout`, `error` share | Run duration | Concurrent child processes |
| Webhooks | Events/min (Stripe, Clerk) | Non-`2xx` responses; signature failures | — | Vendor retry backlog (in vendor dashboards) |
| Studio (Vercel) | Page views | Function/edge errors, JS errors | Core Web Vitals (Vercel Speed Insights) | — |
| Backups | Job runs | Job failures | Job duration | Backup storage size |

### 5.3 Telemetry sources available today

| Source | How to access | Notes |
| --- | --- | --- |
| Container Apps console logs | `az containerapp logs show --type console`, or Log Analytics table `ContainerAppConsoleLogs_CL` | Uvicorn access lines, application `WARNING`/`ERROR`, tracebacks, OTel console spans when `OTEL_EXPORTER_OTLP_ENDPOINT` is set (HZ-9) |
| Container Apps system logs | `--type system`, table `ContainerAppSystemLogs_CL` | Revision provisioning, probe failures, OOM kills, restarts |
| Container Apps metrics | Azure Monitor on the Container App resource | Requests (split by status code category), replica count, restart count, CPU, memory |
| PostgreSQL metrics and logs | Azure Monitor on the server; server logs via diagnostic settings to Log Analytics | Enable `log_min_duration_statement` (§10.3) and pg_stat_statements |
| Vercel | Dashboard → Observability / Logs; Speed Insights | Studio errors and Web Vitals |
| Stripe | Dashboard → Developers → Webhooks → endpoint → attempts | Delivery failures and retries |
| Clerk | Dashboard → Webhooks (Svix) → message attempts | Delivery failures |
| Provider consoles | OpenAI / Anthropic / Google usage dashboards | Spend, rate limits, errors |
| Langfuse | Langfuse project | Treat as unreliable until HZ-8 is fixed |

**[TO PROVISION]** in order of value:

1. Diagnostic settings on the Container Apps environment and PostgreSQL server sending logs and metrics to Log Analytics workspace `$WS`.
2. External synthetic probes (Azure Application Insights standard availability tests or an uptime service) from at least 3 regions: `GET $API_URL/health` every 1 min; `GET $WEB_URL/` every 1 min; authenticated smoke flow (§9.6) every 15 min with a dedicated synthetic learner account.
3. Azure Monitor action group `ag-aimentor-oncall` routing to the paging tool, the ops chat channel, and email.
4. A workbook "AI Mentor — Production" with the panels in §5.5.

### 5.4 Saved Log Analytics queries (KQL)

Save these in the workspace under the folder "AI Mentor".

**Q1 — HTTP status by minute (from Uvicorn access logs)**

```kusto
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| where ContainerAppName_s == "ca-aimentor-api"
| extend status = toint(extract(@"HTTP/[0-9.]+\"\s(\d{3})", 1, Log_s))
| where isnotnull(status)
| summarize total=count(), s5xx=countif(status >= 500), s429=countif(status == 429), s401=countif(status == 401) by bin(TimeGenerated, 1m)
| extend err_rate = todouble(s5xx) / total
| order by TimeGenerated desc
```

**Q2 — Requests by route and status**

```kusto
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h) and ContainerAppName_s == "ca-aimentor-api"
| extend method = extract(@"\"(GET|POST|PATCH|PUT|DELETE|OPTIONS) ", 1, Log_s),
         path = extract(@"\"[A-Z]+ ([^ ?]+)", 1, Log_s),
         status = toint(extract(@"HTTP/[0-9.]+\"\s(\d{3})", 1, Log_s))
| where isnotnull(status)
| extend route = replace_regex(path, @"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{id}")
| summarize count() by method, route, status
| order by count_ desc
```

**Q3 — Tracebacks and errors**

```kusto
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h) and ContainerAppName_s == "ca-aimentor-api"
| where Log_s has_any ("Traceback", " ERROR ", "Exception")
| project TimeGenerated, RevisionName_s, ContainerGroupName_s, Log_s
| order by TimeGenerated desc
| take 200
```

**Q4 — Model provider failures by provider**

```kusto
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(6h) and ContainerAppName_s == "ca-aimentor-api"
| where Log_s has "model provider" and Log_s has "failed"
| extend provider = extract(@"model provider _(\w+) failed", 1, Log_s)
| summarize failures=count() by provider, bin(TimeGenerated, 5m)
```

**Q5 — Platform events: restarts, probe failures, OOM**

```kusto
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(6h) and ContainerAppName_s == "ca-aimentor-api"
| where Log_s has_any ("probe", "OOM", "Killed", "BackOff", "Error", "failed")
| project TimeGenerated, RevisionName_s, Reason_s, Log_s
| order by TimeGenerated desc
```

**Q6 — Lab outcomes (from timeouts in stderr appearing in logs, or from the database; prefer §8.4)**

**Q7 — Webhook failures**

```kusto
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h) and ContainerAppName_s == "ca-aimentor-api"
| where Log_s has_any ("/api/v1/webhooks/stripe", "/api/v1/webhooks/clerk")
| extend status = toint(extract(@"HTTP/[0-9.]+\"\s(\d{3})", 1, Log_s))
| summarize count() by status, hook = iff(Log_s has "stripe", "stripe", "clerk"), bin(TimeGenerated, 1h)
```

Run any query from the CLI:

```bash
az monitor log-analytics query -w "$WS" --analytics-query "<KQL>" -o table
```

Uvicorn access logs do not include duration. Until request-duration logging is added **[CODE CHANGE]** (middleware logging `method path status duration_ms trace_id` as JSON), use ingress metrics and synthetic probe timings for latency.

### 5.5 Dashboard panels (workbook)

1. Synthetic availability (API, studio) — last 24 h, by region.
2. Requests/min and `5xx`/`429`/`401` rates (Q1).
3. Top routes by volume and error (Q2).
4. Replica count, CPU %, memory %, restarts (Container Apps metrics).
5. PostgreSQL CPU, memory, storage %, active connections vs max, failed connections.
6. Model provider failures (Q4) and curriculum-fallback share.
7. Lab outcomes: ok / error / rejected / timeout (from `code_submissions`, §8.4, exported hourly) **[TO PROVISION]**.
8. Webhook delivery (Q7).
9. Backup freshness: last logical dump age, last on-demand backup.
10. Daily model spend by provider (provider APIs or manual daily entry until automated).

---

## 6. Alert Thresholds

All alerts route through `ag-aimentor-oncall`. "Critical" pages the on-call; "Warning" posts to the ops channel only. Every alert description must include a link to the runbook section in the last column.

### 6.1 API and platform

| Alert | Signal | Warning | Critical | Window / evaluation | Runbook |
| --- | --- | --- | --- | --- | --- |
| API down (synthetic) | `GET /health` from ≥ 2 of 3 regions fails or > 5 s | 2 consecutive failures | 3 consecutive failures (≈ 3 min) | 1 min | TG-01, TG-03 |
| Studio down (synthetic) | `GET $WEB_URL/` non-`200` | 2 consecutive | 3 consecutive | 1 min | TG-13 |
| 5xx rate | `5xx / total` (Q1), only if total ≥ 20 req/5 min | > 2% | > 5% | 5 min, every 1 min | TG-01 |
| 429 rate | `429 / total` | > 5% | > 15% | 10 min | TG-02 |
| 401 surge | `401 / total` (authenticated routes) | > 10% | > 30% | 10 min | TG-05 |
| Health latency | Synthetic `/health` duration | > 1 s p95 | > 3 s p95 | 10 min | TG-03 |
| Tutor latency | `/api/v1/chat` p95 (ingress or smoke test) | > 8 s | > 15 s | 15 min | TG-03, TG-04 |
| Replica restarts | Restart count | ≥ 3 in 15 min | ≥ 6 in 15 min or any revision `Unhealthy` | 5 min | TG-07 |
| CPU | Container CPU % (avg across replicas) | > 70% for 10 min | > 90% for 5 min | 1 min | §10.2 |
| Memory | Container memory % | > 75% | > 90% | 5 min | TG-15 |
| Replicas at max | Replica count == max replicas | 10 min | 30 min | 5 min | §10.2 |
| Revision provisioning failed | System log `Failed` on provisioning | — | Any | Immediate | TG-07 |
| Tracebacks | Q3 count | > 10 / 5 min | > 50 / 5 min | 5 min | TG-01 |

### 6.2 Database

| Alert | Metric | Warning | Critical | Window | Runbook |
| --- | --- | --- | --- | --- | --- |
| CPU | `cpu_percent` | > 70% | > 90% | 15 min | TG-06, §10.3 |
| Memory | `memory_percent` | > 80% | > 95% | 15 min | §10.3 |
| Storage | `storage_percent` | > 75% | > 90% | 15 min | TG-14 |
| Connections | `active_connections / max_connections` | > 70% | > 90% | 5 min | TG-06 |
| Failed connections | `connections_failed` | > 5 / 5 min | > 50 / 5 min | 5 min | TG-06 |
| Transaction ID wraparound | `maximum_used_transactionIDs` | > 1,000,000,000 | > 1,500,000,000 | 1 h | TG-14 |
| Replication / HA | HA state not `Healthy` | — | Any | Immediate | §11.6 |
| Long-running query | Query > 60 s (pg_stat_activity probe) | > 60 s | > 300 s | 5 min | TG-06 |

Example creation:

```bash
PG_ID=$(az postgres flexible-server show -g "$RG" -n "$PG" --query id -o tsv)
AG_ID=$(az monitor action-group show -g "$RG" -n ag-aimentor-oncall --query id -o tsv)
az monitor metrics alert create -g "$RG" -n "pg-storage-critical" --scopes "$PG_ID" \
  --condition "avg storage_percent > 90" --window-size 15m --evaluation-frequency 5m \
  --severity 1 --action "$AG_ID" --description "Runbook: docs/Runbook.md#TG-14"
az monitor metrics alert create -g "$RG" -n "pg-connections-critical" --scopes "$PG_ID" \
  --condition "max active_connections > <0.9 * max_connections>" --window-size 5m --evaluation-frequency 1m \
  --severity 1 --action "$AG_ID" --description "Runbook: docs/Runbook.md#TG-06"
```

### 6.3 AI, lab, and business flows

| Alert | Signal | Warning | Critical | Window | Runbook |
| --- | --- | --- | --- | --- | --- |
| Provider failures | Q4 count for any provider | > 5 / 5 min | > 25 / 5 min | 5 min | TG-04 |
| All providers failing | Chat replies served by curriculum fallback while `llm: external` | > 10% of chats | > 50% of chats | 10 min | TG-04 |
| Model spend | Daily spend vs daily budget (monthly budget / 30) | > 80% | > 120% | Hourly | TG-12 |
| Lab timeouts | `code_submissions.status='error'` with stderr "Timed out" share | > 20% | > 50% | 30 min | TG-09 |
| Lab rejections spike | `status='rejected'` per user | > 30 / hour single user | > 100 / hour single user | 1 h | TG-16, TG-17 |
| Stripe webhook failures | Non-`2xx` (Q7) or Stripe dashboard failure email | Any `5xx` | > 5 in 1 h, or any `503` (not configured) | 15 min | TG-10 |
| Clerk webhook failures | Non-`2xx` | Any | > 10 in 1 h | 15 min | TG-11 |
| Prompt-injection flags | Guardrail rejections per user | > 20 / hour | > 100 / hour | 1 h | TG-16 |
| Research analysis duration | `/api/v1/research/analyze` p95 | > 20 s | > 60 s | 30 min | TG-08 |

### 6.4 Backups and security

| Alert | Signal | Critical when | Runbook |
| --- | --- | --- | --- |
| Logical backup missing | No new blob in `pg-logical` | > 26 h | §3.3 |
| Logical backup job failed | Container Apps Job execution failed | Any | §3.3 |
| PITR retention drift | `backupRetentionDays` ≠ 35 | Daily check fails | §3.2 |
| Key Vault secret near expiry | Expiry date set on secret | < 14 days (warning), < 3 days (critical) | §11.8 |
| TLS certificate expiry | API and studio certificate | < 21 days (warning), < 7 days (critical) | §9.3 |
| Dev auth in production | `X-Dev-User-Id` accepted (smoke test sends it and expects `401`) | Any success | §11.8, Security |
| Admin role change | Any `PATCH /api/v1/admin/users/{id}` | Notify ops channel (informational) | — |

### 6.5 Alert hygiene

- Every critical alert must be actionable: if an alert fires and no action was needed, tune or delete it within one week.
- Review alert volume weekly. Target: ≤ 2 pages per on-call week outside real incidents.
- Silence alerts during planned maintenance using Azure Monitor alert processing rules with an end time; never disable rules.

---

## 7. Troubleshooting Guides

Each guide: **Symptoms → Likely causes → Diagnose → Fix → Verify.**

### TG-01 — API returning 5xx

**Symptoms:** `5xx` alert; learners see "Something went wrong"; tracebacks in logs.

**Likely causes:** bad deploy; database unreachable or saturated; unhandled exception in a route; provider SDK exception not caught; JWKS failure (TG-05).

**Diagnose:**
1. Did it start with a deploy? Compare the error start time with the newest revision's `createdTime` (§0.2 step 2).
2. Find the dominant route and error (Q2, Q3).
3. `curl $API_URL/health`. If it fails with a DB error → TG-06.
4. Group tracebacks by exception class:
   ```kusto
   ContainerAppConsoleLogs_CL
   | where TimeGenerated > ago(30m) and ContainerAppName_s == "ca-aimentor-api"
   | where Log_s matches regex @"^\w+(\.\w+)*(Error|Exception):"
   | summarize count() by tostring(split(Log_s, ":")[0])
   ```

**Fix:**
- Started after deploy → roll back (§11.1). Root-cause later.
- Database → TG-06.
- One route only, not deploy-related → assess impact; if severe, roll back or hotfix.

**Verify:** `5xx` rate < 1% for 15 minutes; smoke test passes.

### TG-02 — Many learners receive `429 Too many requests`

**Symptoms:** `429` alert; learners hit limits after a few actions; unrelated users throttled at the same time.

**Likely causes:**
- **HZ-2:** all traffic appears to come from the ingress proxy IP, so every learner shares one 60/min (20/min AI) bucket per process.
- Genuine abuse from one IP.
- Limits too low for real usage.

**Diagnose:**
1. Check which client addresses Uvicorn sees:
   ```kusto
   ContainerAppConsoleLogs_CL
   | where TimeGenerated > ago(15m) and ContainerAppName_s == "ca-aimentor-api"
   | extend client = extract(@"INFO:\s+([0-9a-fA-F\.:]+):\d+ - ", 1, Log_s)
   | where isnotempty(client)
   | summarize requests=count() by client
   | order by requests desc
   ```
   If one or a handful of private addresses (10.x, 100.x, 172.16–31.x) account for nearly all traffic, it is HZ-2.
2. If one public IP dominates, it is abuse → TG-16.

**Fix for HZ-2 (no image change needed):** Uvicorn reads `FORWARDED_ALLOW_IPS` from the environment and then uses `X-Forwarded-For` for `request.client`. Only do this because the Container App is reachable solely through its ingress.

```bash
az containerapp update -n "$APP" -g "$RG" --set-env-vars FORWARDED_ALLOW_IPS="*" \
  --revision-suffix "fwd$(date -u +%H%M)"
```

Re-run the diagnostic query; client addresses should now be diverse public IPs.

**Fix for limits too low (temporary):**

```bash
az containerapp update -n "$APP" -g "$RG" \
  --set-env-vars RATE_LIMIT_PER_MINUTE=120 AI_RATE_LIMIT_PER_MINUTE=40
```

Remember HZ-3: the effective limit is per process. Record any change in the incident timeline and revert after the incident.

**Verify:** `429` rate < 2%; synthetic smoke user not throttled.

### TG-03 — API slow or hung; `/health` times out

**Symptoms:** health latency alert; all routes slow, including non-AI routes; CPU often *low*; replicas may be restarted by probes.

**Likely causes:**
- **HZ-1:** a model provider is slow or hanging; sync routes wait on it with long SDK timeouts and retries; the 40-thread pool per worker is exhausted.
- Embedding calls during research analysis (HZ-5) holding threads.
- Slow DB queries or lock waits holding threads (TG-06).
- Many concurrent lab runs (3 s each).

**Diagnose:**
1. CPU low + latency high = threads waiting on I/O (provider, DB). CPU high = compute (TG-15 / §10.2).
2. Provider status pages (§12.3) and Q4 for failures. Slow-but-not-failing providers do not log failures; check provider dashboards for latency.
3. Live view inside a replica:
   ```bash
   az containerapp exec -n "$APP" -g "$RG" --command "sh"
   # inside the container:
   python - <<'PY'
   import socket, ssl, time
   for host in ["api.openai.com", "api.anthropic.com", "generativelanguage.googleapis.com"]:
       t = time.time()
       try:
           s = socket.create_connection((host, 443), timeout=5)
           ssl.create_default_context().wrap_socket(s, server_hostname=host).close()
           print(host, "tls ok", round(time.time() - t, 2), "s")
       except Exception as e:
           print(host, "FAILED", e)
   PY
   ```
4. Database lock waits: §8.3 queries Q-DB2, Q-DB3.

**Fix:**
1. Identify the slow provider and **disable it** by removing its key so the router skips it (§11.4). If OpenAI is removed, embeddings switch to the local hash model; research analysis stays consistent because it re-embeds query and chunks with the same model each time.
2. Restart replicas to free stuck threads (§11.2).
3. If the DB is the cause → TG-06.
4. Scale out temporarily (§10.2) — buys threads but does not fix a hung provider.

**Verify:** `/health` < 500 ms; chat p95 back under SLO; no growth in stuck requests.

**Permanent fix:** **[CODE CHANGE]** explicit client timeouts (≈ 20 s completion, ≈ 10 s embeddings) and `max_retries ≤ 1`; move provider calls off the shared pool (async clients).

### TG-04 — Tutor answers only from the curriculum ("limited" or generic replies)

**Symptoms:** learners report repetitive or scripted replies; `/health` shows `llm: "curriculum"` or `external` with Q4 failures.

**Likely causes:** model keys missing or expired; all providers failing (quota, billing, outage); outbound network blocked; model name retired (`OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL`).

Note: Socratic stages 0 and 1 are scripted by design (Architecture.md). Scripted opening questions are **not** an incident.

**Diagnose:**
1. `/health`: `llm: "curriculum"` → no key configured. Check secrets exist:
   ```bash
   az containerapp secret list -n "$APP" -g "$RG" --query "[].name" -o tsv
   az containerapp show -n "$APP" -g "$RG" --query "properties.template.containers[0].env[?contains(name,'API_KEY') || contains(name,'MODEL')].{name:name,secretRef:secretRef,value:value}" -o table
   ```
2. Q4 for failing providers, then read a full traceback (Q3) — typical messages: `AuthenticationError` (key revoked), `RateLimitError`/`insufficient_quota` (billing), `NotFoundError: model` (model retired), connection errors (network).
3. Test a key from inside a replica without printing it:
   ```bash
   az containerapp exec -n "$APP" -g "$RG" --command "sh"
   python -c "from app.core.config import get_settings; from app.services.llm import ProviderRouter; print(ProviderRouter(get_settings()).complete(system='Reply with OK', messages=[('user','ping')], max_tokens=5))"
   ```
   `None` means every configured provider failed; the logs show why.

**Fix:**
- Key revoked/expired → rotate (§11.8).
- Quota/billing → AI lead raises the limit with the provider; meanwhile ensure at least one other provider key is configured.
- Model retired → set the env var to a supported model and create a new revision:
  ```bash
  az containerapp update -n "$APP" -g "$RG" --set-env-vars OPENAI_MODEL=<model>
  ```
- Outage → rely on failover; if none left, accept curriculum mode and post a status update (SEV2).

**Verify:** the test command returns text; learners receive model replies after stage 1.

### TG-05 — Everyone gets `401`, or sign-in "works" but the API rejects it

**Symptoms:** `401` surge; studio shows signed-in state but API calls fail; or slow `500`s on all authenticated routes.

**Likely causes:**
- `CLERK_ISSUER` or `CLERK_JWKS_URL` wrong after a Clerk instance change (dev ↔ prod keys).
- Clerk JWKS endpoint unreachable (HZ-10) → `500` after the key cache expires.
- Studio using a different Clerk instance than the API expects.
- Clock skew (rare on Azure).
- Studio still sending `X-Dev-User-Id` without a bearer token (dev switcher left on; `NEXT_PUBLIC_DEV_AUTH` set in the Vercel production build).

**Diagnose:**
1. Decode a failing token's claims (from a browser session; never paste tokens into shared channels):
   ```bash
   echo "<jwt>" | cut -d. -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | jq '{iss, sub, exp, azp}'
   ```
   Compare `iss` with the configured `CLERK_ISSUER`.
2. From inside a replica, fetch the JWKS:
   ```bash
   python -c "import os,urllib.request;print(urllib.request.urlopen(os.environ['CLERK_JWKS_URL'],timeout=5).status)"
   ```
3. Check Clerk status (§12.3).
4. Check the studio build env in Vercel for `NEXT_PUBLIC_DEV_AUTH` (must be empty in production) and the Clerk publishable key (must be the production instance).

**Fix:**
- Wrong issuer/JWKS → correct the env vars (`az containerapp update --set-env-vars CLERK_ISSUER=... CLERK_JWKS_URL=...`).
- Clerk outage → SEV2; nothing to fail over to. Post status. Valid cached keys keep working for a few minutes only.
- Studio misconfigured → fix Vercel env and redeploy the studio (§11.3).

**Verify:** smoke test sign-in step passes; `401` rate back to baseline (< 2%).

### TG-06 — Database connection errors, saturation, or lock waits

**Symptoms:** `/health` fails with `OperationalError`; `connections_failed` alert; `too many connections`; `remaining connection slots are reserved`; slow everything.

**Likely causes:** total pool size across replicas exceeds `max_connections` (§10.3 formula); a long transaction holding locks (migration, bulk fix, large synchronous ingestion); server CPU saturated by an inefficient query; server restarting (maintenance, failover); network/firewall change.

**Diagnose:**
1. Server state and metrics:
   ```bash
   az postgres flexible-server show -g "$RG" -n "$PG" --query "{state:state, ha:highAvailability.state}" -o table
   az monitor metrics list --resource "$PG_ID" --metric active_connections cpu_percent memory_percent --interval PT1M --offset 30m -o table
   ```
2. Connections by application and state, long transactions, and blockers: §8.3 Q-DB1 to Q-DB3.
3. Replica count × workers × pool (15) vs `max_connections`:
   ```bash
   az postgres flexible-server parameter show -g "$RG" -s "$PG" --name max_connections --query value -o tsv
   ```

**Fix:**
- Blocking or runaway query → cancel, then terminate if needed (§8.3 Q-DB4). Get IC approval before terminating a migration.
- Pool exhaustion → reduce replicas or workers temporarily, or raise `max_connections` (requires restart on some tiers; schedule) — see §10.3.
- CPU saturation from one query → cancel; add index or fix code later.
- Server restarting (planned maintenance or HA failover) → wait; SQLAlchemy `pool_pre_ping` recovers connections automatically. Restart replicas if errors persist > 5 min after the server is `Ready`.

**Verify:** `/health` OK; active connections < 70% of max; no blocked sessions.

### TG-07 — Replicas crash-loop or a new revision never becomes healthy

**Symptoms:** revision `Unhealthy` or `Failed`; restart count rising; system logs show `BackOff`; deploy stuck.

**Likely causes:**
- `production_guard` refusing to start: `DEV_AUTH must be disabled in production`, `CLERK_JWKS_URL and CLERK_ISSUER are required in production`, `DATABASE_URL must be PostgreSQL in production`, `QDRANT_URL must be an HTTP server in production`.
- `alembic upgrade head` failing (migration error, DB unreachable, lock timeout, concurrent migration from another replica — HZ-4).
- Seed upsert conflict during concurrent start (HZ-4).
- Missing secret referenced by env (`secretref` to a non-existent secret).
- OOM during start.
- Image tag does not exist or registry credentials expired.

**Diagnose:**
```bash
az containerapp logs show -n "$APP" -g "$RG" --type system --tail 100
az containerapp logs show -n "$APP" -g "$RG" --type console --revision <rev> --tail 200
```
Search the console output for `ValueError`, `alembic`, `IntegrityError`, `ImportError`.

**Fix:**
- Config error → correct env/secret; create a new revision.
- Migration failure → keep traffic on the previous healthy revision (it is still serving if you use multiple-revision mode; §11.1). Inspect `SELECT version_num FROM alembic_version;`. Fix forward with a corrected migration, or restore (§4.2) if the migration partially applied destructive changes. Never edit `alembic_version` by hand without IC approval and a fresh on-demand backup.
- Concurrent start → scale the new revision to 1 replica until migrations and seed finish, then scale out:
  ```bash
  az containerapp update -n "$APP" -g "$RG" --min-replicas 1 --max-replicas 1
  # after healthy:
  az containerapp update -n "$APP" -g "$RG" --min-replicas 2 --max-replicas 10
  ```
- Image pull error → confirm the tag exists (`gh api /user/packages/container/<pkg>/versions` or the GHCR UI) and the registry credential is valid.

**Verify:** revision `Healthy`; restart count stable for 15 minutes; smoke test passes.

### TG-08 — Research upload or analysis slow, failing, or expensive

**Symptoms:** `POST /api/v1/research/documents` or `/analyze` takes minutes or returns `5xx`; embedding spend spikes; thread exhaustion (TG-03).

**Likely causes:**
- **HZ-5:** analysis embeds every chunk on every question. A 10 MB text file is ~13,000 chunks.
- **HZ-13:** ingestion runs in the request; large files hold a thread and DB transaction.
- Embedding provider error: with an OpenAI key set, embedding failures raise and fail the upload (by design, to avoid mixing vector spaces).
- Unparseable PDF (scanned, no text layer) → "no extractable text".

**Diagnose:**
```sql
-- Largest documents by chunk count
SELECT d.id, d.user_id, d.filename, count(c.id) AS chunks, d.created_at
FROM research_documents d JOIN document_chunks c ON c.document_id = d.id
GROUP BY d.id ORDER BY chunks DESC LIMIT 20;
```
Check Q3 for `openai` exceptions during `/research/*` requests.

**Fix:**
- A single huge document hammering the API → contact/limit the user (TG-16); as a stopgap, delete the document after notifying the user if it threatens platform stability (IC approval; audit note).
- Embedding provider failing → wait or, if prolonged, remove `OPENAI_API_KEY` (§11.4) to switch to hash embeddings (also disables OpenAI completions).
- Scanned PDFs → expected; OCR is out of scope; support explains to the learner.

**Verify:** analysis p95 < 20 s; embedding spend back to baseline.

**Permanent fix:** persist vectors and query Qdrant (HZ-5/HZ-6); move ingestion to a job queue; cap chunks per document by tier.

### TG-09 — Coding lab timeouts or errors

**Symptoms:** many `Timed out after 3 seconds.`; learners report correct code failing; lab latency high.

**Likely causes:** CPU contention on replicas (lab runs share the API's CPU); a project whose reference solution is near the 3 s limit; high concurrent lab usage; regression in the harness.

**Diagnose:**
```sql
SELECT status,
       count(*) FILTER (WHERE stderr LIKE 'Timed out%') AS timeouts,
       count(*) AS total
FROM code_submissions WHERE created_at > now() - interval '1 hour' GROUP BY status;

SELECT p.slug, count(*) AS runs,
       count(*) FILTER (WHERE s.stderr LIKE 'Timed out%') AS timeouts
FROM code_submissions s LEFT JOIN projects p ON p.id = s.project_id
WHERE s.created_at > now() - interval '24 hours'
GROUP BY p.slug ORDER BY timeouts DESC;
```
Correlate with replica CPU.

**Fix:**
- CPU contention → scale out (§10.2) or raise CPU per replica (§10.1).
- One project → check its starter/reference code locally with `make api`; fix the project in the catalog and release.
- Harness regression → roll back (§11.1).

**Verify:** timeout share < 5%.

### TG-10 — Payments succeed but learners are not upgraded (Stripe)

**Symptoms:** learner paid but still Free; Stripe dashboard shows webhook failures; Stripe failure emails.

**Likely causes:** `STRIPE_WEBHOOK_SECRET` wrong or rotated (→ `400 Invalid Stripe signature`); Stripe keys not configured (→ `503`); webhook endpoint URL wrong; the event's `clerk_id` / customer does not match a local user (handler silently does nothing); API down during delivery (Stripe retries for up to 3 days).

**Diagnose:**
1. Stripe Dashboard → Developers → Webhooks → endpoint → recent attempts: note status codes.
2. Q7 for webhook statuses.
3. Look up the learner:
   ```sql
   SELECT id, clerk_id, email, stripe_customer_id, subscription_status FROM users WHERE email = '<email>';
   ```
   Compare `clerk_id` with the Checkout Session's `client_reference_id` / `metadata.clerk_id` in Stripe.

**Fix:**
- Signature error → set the correct signing secret from the Stripe endpoint page (§11.8), new revision, then **resend** failed events from the Stripe dashboard (or `stripe events resend <evt_id>`).
- `503` → configure `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`.
- No matching user → correct manually after verifying the payment in Stripe (record in ticket):
  ```sql
  UPDATE users SET stripe_customer_id = '<cus_...>', subscription_status = 'active' WHERE id = '<uuid>';
  ```

**Verify:** endpoint attempts show `200`; learner's `/me` shows the new status.

### TG-11 — New users or role changes from Clerk not reflected

**Symptoms:** Clerk dashboard shows webhook failures; user profile name/email stale.

Impact is usually low: users are also upserted on their first authenticated request.

**Likely causes:** `CLERK_WEBHOOK_SECRET` missing (`503`) or wrong (`400 Invalid Clerk signature`); endpoint URL wrong.

**Fix:** correct the secret (§11.8); replay failed messages from Clerk Dashboard → Webhooks → endpoint → message attempts → Resend. Note: `user.deleted` is not handled (HZ-14); deletions follow §11.9.

### TG-12 — Model spend spike

**Symptoms:** spend alert; provider dashboard shows unusual usage.

**Likely causes:** abuse (scripted chat), runaway research analyses (HZ-5), a prompt change that increased tokens, retries amplifying calls (HZ-1), leaked API key used outside the platform.

**Diagnose:**
1. Provider dashboard: usage by key and by model; compare with our request volume (Q2 for `/chat`, `/research/analyze`, `/quiz`).
2. Heavy users:
   ```sql
   SELECT c.user_id, count(m.id) AS messages_24h
   FROM messages m JOIN conversations c ON c.id = m.conversation_id
   WHERE m.created_at > now() - interval '24 hours' AND m.role = 'user'
   GROUP BY c.user_id ORDER BY messages_24h DESC LIMIT 20;
   ```
3. If provider usage far exceeds our request volume → **assume the key is leaked**: SEV1 security branch (§1.5).

**Fix:** leaked key → rotate immediately (§11.8). Abuse → TG-16. HZ-5 → TG-08. Set a hard monthly limit in each provider console as a backstop.

### TG-13 — Studio (Vercel) down or showing errors

**Symptoms:** studio synthetic fails; blank pages; build failed.

**Diagnose:** Vercel status (§12.3); Vercel dashboard → Deployments (is production the expected deployment?) → Logs; browser console for CORS errors (TG-18) or `NEXT_PUBLIC_API_URL` pointing to the wrong API.

**Fix:** instant rollback to the previous production deployment (§11.3). If CORS → TG-18. If the API is down, the studio fails too → TG-01.

### TG-14 — Database storage full or transaction ID wraparound risk

**Symptoms:** storage alert; writes failing with `could not extend file` / read-only mode; `maximum_used_transactionIDs` alert.

**Diagnose:** table sizes and dead tuples (§8.3 Q-DB5, Q-DB6).

**Fix:**
- Storage: enable or confirm **storage autogrow**, or increase storage now (online, cannot be reduced later):
  ```bash
  az postgres flexible-server update -g "$RG" -n "$PG" --storage-auto-grow Enabled
  az postgres flexible-server update -g "$RG" -n "$PG" --storage-size 256
  ```
- Bloat in hot tables (`messages`, `xp_events`, `users` due to HZ-11) → `VACUUM (VERBOSE, ANALYZE) <table>;` during low traffic; tune autovacuum (§10.3).
- Wraparound: run `VACUUM (FREEZE, VERBOSE) <table>;` on the tables with the oldest `relfrozenxid` (§8.3 Q-DB7). Engage Azure support if > 1.5 billion.

### TG-15 — Memory growth or OOM kills

**Symptoms:** memory alert; system logs show OOM/`Killed`; periodic restarts.

**Likely causes:** large uploads parsed in memory (10 MB file → much larger parsed text and chunk lists); many concurrent requests holding large documents; leak in a dependency.

**Fix:** increase memory per replica (§10.1); restart replicas (§11.2); if correlated with uploads, cap at the proxy and limit concurrent uploads; capture a heap profile in staging for leaks.

### TG-16 — Abuse: scraping, scripted chat, brute force, injection waves

**Symptoms:** one user or IP dominates traffic (TG-02 query); spike in prompt-injection rejections; lab rejection spikes; spend spike.

**Fix:**
1. Identify user id(s) via §8.4 queries and IP(s) via TG-02 query.
2. Block IPs at the edge (Container Apps ingress IP restrictions):
   ```bash
   az containerapp ingress access-restriction set -n "$APP" -g "$RG" \
     --rule-name "block-<ip>" --ip-address "<ip>/32" --action Deny --description "INC-<id>"
   ```
   Note: adding the first `Deny` rule leaves all other traffic allowed; adding an `Allow` rule switches to allow-list mode. Double-check before applying.
3. Disable the account: ban the user in Clerk (dashboard → Users → Ban) so new sessions fail; existing JWTs expire within minutes.
4. Record everything; review blocks after 7 days.

### TG-17 — Suspected sandbox bypass

**Symptoms:** lab output containing environment data, file listings, network results; unusual processes; Security report.

This is a **SEV1 security incident** (§1.5). Because learner code runs inside the API container (HZ-12):

1. Disable the lab immediately. Fastest option without a code change: block the lab routes at ingress is not possible by path, so roll out a revision with the lab disabled **[CODE CHANGE: add `LAB_ENABLED` flag]**; until that flag exists, roll back to a revision without the vulnerable change or scale to zero if active exploitation is confirmed (IC decision).
2. Rotate **all** secrets available to the API container (§11.8): database URL, model keys, Stripe, Clerk webhook secret, Langfuse.
3. Preserve the offending `code_submissions` rows and logs.
4. Replace the replicas (new revision) to discard any modified container state.
5. Review database audit (who did what during the window) with Security.

### TG-18 — CORS errors in the browser

**Symptoms:** browser console: "blocked by CORS policy"; API logs show `OPTIONS` requests.

**Cause:** `CORS_ORIGINS` does not include the studio origin exactly (scheme + host + port, no trailing slash), e.g. after adding a custom domain or using a Vercel preview URL.

**Fix:**
```bash
az containerapp update -n "$APP" -g "$RG" --set-env-vars CORS_ORIGINS="https://<domain>,https://www.<domain>"
```
Billing return URLs must start with one of these origins, so checkout also fails with `400 Return URL must stay on this application` when this is wrong.

---

## 8. Production Diagnostics

### 8.1 Access rules

- Production access is through Azure RBAC with Entra ID; just-in-time elevation (Privileged Identity Management) for `Contributor` on `$RG` **[TO PROVISION]**.
- Every interactive production session (exec, psql) is announced in the ops channel with the reason, and in the incident channel during incidents.
- Read-only first: use the `ops_ro` database role for diagnostics; use the admin role only for approved fixes.
- Never paste secrets, JWTs, or learner content into chat, tickets, or AI tools. Refer to learners by user id.

### 8.2 Container diagnostics

```bash
# Revisions, traffic, health
az containerapp revision list -n "$APP" -g "$RG" -o table
az containerapp show -n "$APP" -g "$RG" --query "{fqdn:properties.configuration.ingress.fqdn, mode:properties.configuration.activeRevisionsMode, min:properties.template.scale.minReplicas, max:properties.template.scale.maxReplicas, cpu:properties.template.containers[0].resources.cpu, mem:properties.template.containers[0].resources.memory, image:properties.template.containers[0].image}" -o table

# Replicas of a revision
az containerapp replica list -n "$APP" -g "$RG" --revision <rev> -o table

# Logs for a specific replica
az containerapp logs show -n "$APP" -g "$RG" --revision <rev> --replica <replica> --tail 300

# Shell into a replica
az containerapp exec -n "$APP" -g "$RG" --revision <rev> --replica <replica> --command "sh"

# Export logs for evidence (incident window)
az monitor log-analytics query -w "$WS" --analytics-query \
  "ContainerAppConsoleLogs_CL | where TimeGenerated between (datetime(2026-10-13T10:00:00Z) .. datetime(2026-10-13T11:00:00Z)) | where ContainerAppName_s == 'ca-aimentor-api'" \
  -o json > evidence/inc-<id>-console.json
```

Inside a replica (Python 3.12, user `mentor`, working directory `/app`):

```bash
# Effective configuration without printing secrets
python - <<'PY'
from app.core.config import get_settings
s = get_settings()
print("env", s.app_env, "dev_auth", s.resolved_dev_auth)
print("db", s.database_url.split("@")[-1])
print("qdrant", s.qdrant_url.split("@")[-1])
print("clerk_issuer", s.clerk_issuer)
print("providers", {"openai": bool(s.openai_api_key), "anthropic": bool(s.anthropic_api_key), "gemini": bool(s.gemini_api_key)})
print("models", s.openai_model, s.anthropic_model, s.gemini_model, "embed", s.embedding_model)
print("limits", s.rate_limit_per_minute, s.ai_rate_limit_per_minute, "cors", s.origins)
print("stripe", bool(s.stripe_secret_key), bool(s.stripe_webhook_secret), "clerk_webhook", bool(s.clerk_webhook_secret))
PY

# Alembic state
alembic current
alembic history | head -5

# Process view (thread count of the Uvicorn worker is a proxy for pool saturation)
ps -eo pid,ppid,nlwp,rss,etime,cmd | head -20

# Is a lab child process stuck?
ps -eo pid,etime,cmd | grep -E "harness.py" | grep -v grep

# Lab sanity
python -c "from app.services.sandbox_runner import run_student_code as r; print(r('print(sum(range(10)))'))"
python -c "from app.services.sandbox_runner import run_student_code as r; print(r('import os'))"   # expect status rejected
```

### 8.3 Database diagnostics (SQL)

Connect with the read-only role:

```bash
psql "host=$PG_HOST port=5432 dbname=mentor user=ops_ro sslmode=require"
```

**Q-DB1 — Connections by state and application**

```sql
SELECT usename, application_name, client_addr, state, count(*)
FROM pg_stat_activity WHERE datname = 'mentor'
GROUP BY 1,2,3,4 ORDER BY count(*) DESC;
SHOW max_connections;
```

**Q-DB2 — Long-running queries and transactions**

```sql
SELECT pid, usename, state, now() - xact_start AS xact_age, now() - query_start AS query_age,
       wait_event_type, wait_event, left(query, 200) AS query
FROM pg_stat_activity
WHERE datname = 'mentor' AND state <> 'idle' AND (now() - query_start) > interval '10 seconds'
ORDER BY query_age DESC;

-- Idle-in-transaction sessions hold locks and pool slots
SELECT pid, now() - state_change AS idle_for, left(query, 200)
FROM pg_stat_activity WHERE state = 'idle in transaction' ORDER BY idle_for DESC;
```

**Q-DB3 — Who blocks whom**

```sql
SELECT blocked.pid AS blocked_pid, left(blocked.query, 120) AS blocked_query,
       blocking.pid AS blocking_pid, left(blocking.query, 120) AS blocking_query,
       now() - blocking.xact_start AS blocking_xact_age
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
```

**Q-DB4 — Cancel / terminate (admin role, IC approval for terminate)**

```sql
SELECT pg_cancel_backend(<pid>);     -- cancel the current query, keep the session
SELECT pg_terminate_backend(<pid>);  -- end the session (rolls back its transaction)
```

**Q-DB5 — Table and index sizes**

```sql
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS total,
       pg_size_pretty(pg_relation_size(relid)) AS table, n_live_tup, n_dead_tup
FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;
```

**Q-DB6 — Autovacuum health**

```sql
SELECT relname, n_dead_tup, n_live_tup,
       round(100.0 * n_dead_tup / greatest(n_live_tup, 1), 1) AS dead_pct,
       last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 20;
```

**Q-DB7 — Transaction ID age**

```sql
SELECT relname, age(relfrozenxid) AS xid_age FROM pg_class
WHERE relkind = 'r' ORDER BY age(relfrozenxid) DESC LIMIT 10;
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;
```

**Q-DB8 — Slowest statements (requires pg_stat_statements, §10.3)**

```sql
SELECT calls, round(mean_exec_time::numeric, 1) AS mean_ms, round(total_exec_time::numeric / 1000, 1) AS total_s,
       rows, left(query, 160) AS query
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;
```

**Q-DB9 — Unused or missing indexes (sequential scans on large tables)**

```sql
SELECT relname, seq_scan, idx_scan, n_live_tup
FROM pg_stat_user_tables WHERE n_live_tup > 10000 ORDER BY seq_scan DESC LIMIT 20;
```

### 8.4 Application-level diagnostics (SQL)

```sql
-- Activity in the last hour
SELECT
  (SELECT count(*) FROM messages WHERE created_at > now() - interval '1 hour' AND role = 'user') AS chat_msgs,
  (SELECT count(*) FROM quiz_results WHERE created_at > now() - interval '1 hour') AS quizzes_graded,
  (SELECT count(*) FROM code_submissions WHERE created_at > now() - interval '1 hour') AS lab_runs,
  (SELECT count(*) FROM research_documents WHERE created_at > now() - interval '1 hour') AS uploads,
  (SELECT count(*) FROM xp_events WHERE created_at > now() - interval '1 hour') AS xp_events;

-- A learner's recent conversation (incident investigation only; announce access)
SELECT m.created_at, m.role, m.concept_slug, left(m.content, 300)
FROM messages m JOIN conversations c ON c.id = m.conversation_id
WHERE c.user_id = '<uuid>' ORDER BY m.created_at DESC LIMIT 20;

-- XP reconciliation: users whose stored XP differs from their events
SELECT u.id, u.xp, coalesce(e.total, 0) AS events_total
FROM users u LEFT JOIN (SELECT user_id, sum(amount) AS total FROM xp_events GROUP BY user_id) e ON e.user_id = u.id
WHERE u.xp <> coalesce(e.total, 0);

-- Fix one user's XP and level from events (admin role, ticketed)
UPDATE users u SET xp = s.total, level = 1 + s.total / 250
FROM (SELECT user_id, coalesce(sum(amount), 0) AS total FROM xp_events WHERE user_id = '<uuid>' GROUP BY user_id) s
WHERE u.id = s.user_id;

-- Daily XP cap sanity: anyone above 400 today (non-badge) indicates a bug
SELECT user_id, sum(amount) FROM xp_events
WHERE created_at >= date_trunc('day', now()) GROUP BY user_id HAVING sum(amount) > 400;

-- Subscription status distribution and recent changes
SELECT subscription_status, count(*) FROM users GROUP BY 1;
SELECT id, email, subscription_status, updated_at FROM users WHERE stripe_customer_id IS NOT NULL ORDER BY updated_at DESC LIMIT 20;

-- Admin count (must be >= 1)
SELECT id, email, updated_at FROM users WHERE role = 'admin';

-- Lab outcome mix (last 24 h)
SELECT status, count(*) FROM code_submissions WHERE created_at > now() - interval '24 hours' GROUP BY status;

-- Embedding provider mix (detect accidental switch between openai and hash)
SELECT provider, model, dimensions, count(*) FROM embeddings GROUP BY 1,2,3;
```

### 8.5 External dependency probes

```bash
# API from outside
curl -sS -m 10 -o /dev/null -w 'health %{http_code} %{time_total}s\n' "$API_URL/health"
curl -sS -m 10 -o /dev/null -w 'paths %{http_code} %{time_total}s\n' "$API_URL/api/v1/learning-paths"

# Dev auth must be refused in production (expect 401)
curl -sS -o /dev/null -w 'dev-auth %{http_code}\n' -H 'X-Dev-User-Id: demo-admin' "$API_URL/api/v1/me"

# Security headers present
curl -sSI "$API_URL/health" | grep -Ei 'x-content-type-options|x-frame-options|referrer-policy|permissions-policy'

# Clerk JWKS reachable
curl -sS -m 5 -o /dev/null -w 'jwks %{http_code} %{time_total}s\n' "$CLERK_JWKS_URL"

# Qdrant
curl -sS -m 5 -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/readyz"; echo
curl -sS -m 5 -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections" | jq '.result.collections | length'

# TLS expiry
echo | openssl s_client -servername "${API_URL#https://}" -connect "${API_URL#https://}:443" 2>/dev/null | openssl x509 -noout -enddate
```

---

## 9. Service Health Checks

### 9.1 Probe configuration (Container Apps)

Configure these probes on the API container **[TO PROVISION if absent]**. Because `/health` touches the database, using it for liveness would restart every replica during a database blip and make the outage worse.

| Probe | Type | Target | Initial delay | Period | Timeout | Failure threshold |
| --- | --- | --- | --- | --- | --- | --- |
| Startup | TCP | port 8000 | 5 s | 5 s | 3 s | 30 (allows 150 s for migrations and seed) |
| Liveness | TCP | port 8000 | — | 15 s | 3 s | 4 |
| Readiness | HTTP GET | `/health` | — | 10 s | 3 s | 3 |

Readiness removes a replica from load balancing without killing it. Once a lightweight `/livez` and dependency-aware `/ready` exist **[CODE CHANGE]**, switch liveness to `/livez` and readiness to `/ready`.

### 9.2 Component health matrix

| Component | Check | Command / location | Healthy |
| --- | --- | --- | --- |
| API | Health endpoint | `curl $API_URL/health` | `200`, `status: ok`, `env: production`, < 500 ms |
| API | Revision state | `az containerapp revision list` | One active revision with 100% traffic, `Healthy`, replicas ≥ min |
| API | Dev auth refused | §8.5 | `401` |
| API | Model mode | `/health` `llm` | `external` |
| PostgreSQL | Server state | `az postgres flexible-server show` | `Ready`; HA `Healthy` |
| PostgreSQL | Capacity | Azure metrics | CPU < 70%, storage < 75%, connections < 70% |
| Qdrant | Ready | `GET /readyz` | `200` (no learner impact today, HZ-6) |
| Clerk | JWKS | §8.5 | `200` < 1 s |
| Stripe | Webhook endpoint | Stripe dashboard | Last 24 h deliveries `2xx` |
| Clerk webhooks | Endpoint | Clerk dashboard | Last 24 h deliveries `2xx` |
| Model providers | Test completion | TG-04 step 3 | Text returned |
| Studio | Home page | `curl -I $WEB_URL` | `200` |
| Backups | Freshness | §3.7 | All jobs within schedule |
| Certificates | Expiry | §8.5 | > 21 days |

### 9.3 Daily checklist (on-call, start of shift, ≈ 10 minutes)

1. Review alerts and pages from the last 24 h; ensure each has a ticket or a note.
2. Synthetic availability last 24 h ≥ 99.5%.
3. `5xx` rate (Q1, 24 h) < 0.5%; `429` < 2%; no new exception classes (Q3).
4. Revision: expected image tag, `Healthy`, restart count stable.
5. PostgreSQL CPU/storage/connection peaks within warning thresholds.
6. Logical backup from last night present and > 0 bytes.
7. Stripe and Clerk webhook deliveries all `2xx`.
8. Model provider failures (Q4) and yesterday's spend vs budget.
9. Lab timeout share (TG-09 query) < 5%.
10. Post a one-line health summary in the ops channel.

### 9.4 Weekly checklist (Monday)

1. Restore the latest logical dump into the scratch server and run §4.7 (§3.8).
2. Review error budget burn and SLOs (§5.1).
3. Review Q-DB5/Q-DB6: table growth, bloat, autovacuum lag.
4. Review Q-DB8 top 10 statements; open tickets for any regression.
5. Review alert noise; tune or delete non-actionable alerts.
6. Check dependency/security advisories on the running image (`pip-audit`, GitHub Dependabot alerts).
7. Check certificate and secret expiries for the next 30 days.
8. Verify Key Vault soft-delete and purge-protection settings unchanged.
9. Review on-call handover notes and open postmortem action items.

### 9.5 Monthly and quarterly

- Monthly: confirm PITR retention 35 days and geo-redundancy (§3.2); access review of Azure RBAC, Clerk admins, Stripe, Vercel, GHCR, provider consoles; rebuild image on latest base (`python:3.12-slim`) and release; review capacity trends against §10.
- Quarterly: full restore drill (§3.8); DR tabletop for regional outage (§11.7); secret rotation for all long-lived secrets (§11.8); review and update this runbook and the contact roster.

### 9.6 Smoke test (post-deploy and every 15 minutes from the synthetic monitor)

Uses a dedicated synthetic learner in Clerk (`synthetic+prod@<domain>`) excluded from analytics. `TOKEN` is obtained via the Clerk Backend API for that user (sign-in token → session token) by the monitor; never use a real learner's token.

```bash
#!/usr/bin/env bash
set -euo pipefail
API="${API_URL:?}"; H=(-H "Authorization: Bearer ${TOKEN:?}" -H 'Content-Type: application/json')
fail() { echo "SMOKE FAIL: $1"; exit 1; }

curl -fsS -m 5 "$API/health" | jq -e '.status=="ok" and .env=="production"' >/dev/null || fail health
code=$(curl -s -o /dev/null -w '%{http_code}' -H 'X-Dev-User-Id: demo-admin' "$API/api/v1/me"); [ "$code" = 401 ] || fail "dev-auth $code"
curl -fsS -m 5 "${H[@]}" "$API/api/v1/me" | jq -e '.id' >/dev/null || fail me
curl -fsS -m 5 "${H[@]}" "$API/api/v1/learning-paths" | jq -e 'length >= 4' >/dev/null || fail paths
curl -fsS -m 5 "${H[@]}" "$API/api/v1/dashboard" | jq -e '.' >/dev/null || fail dashboard
curl -fsS -m 20 "${H[@]}" -d '{"message":"What is a Markov decision process?","mode":"socratic"}' \
  "$API/api/v1/chat" | jq -e '.conversation_id' >/dev/null || fail chat
QUIZ=$(curl -fsS -m 20 "${H[@]}" -d '{"concept_slug":"mdp","difficulty":"beginner"}' "$API/api/v1/quiz/generate") || fail quiz
echo "$QUIZ" | jq -e '[.. | objects | has("answer_key")] | any | not' >/dev/null || fail "quiz leaks answer_key"
curl -fsS -m 10 "${H[@]}" -d '{"code":"print(sum(range(10)))"}' "$API/api/v1/lab/run" | jq -e '.status=="ok"' >/dev/null || fail lab
curl -fsS -m 10 "${H[@]}" -d '{"code":"import os"}' "$API/api/v1/lab/run" | jq -e '.status=="rejected"' >/dev/null || fail "lab policy"
curl -fsS -m 5 "$API/api/v1/leaderboard" | jq -e 'type=="array"' >/dev/null || fail leaderboard
echo "SMOKE OK"
```

Adjust `concept_slug` to a seeded concept slug if `mdp` is renamed in `catalog.py`. The synthetic user's conversations should be deleted weekly to avoid growth.

---

## 10. Performance Tuning

Every tuning change follows: **measure baseline → change one thing → measure → keep or revert**, recorded in a change ticket with before/after numbers.

### 10.1 Container sizing

Start point for production: `--cpu 1.0 --memory 2Gi` per replica, min 2 replicas (zone redundancy), max 10.

```bash
az containerapp update -n "$APP" -g "$RG" --cpu 1.0 --memory 2Gi --min-replicas 2 --max-replicas 10
```

Raise CPU when lab timeouts correlate with CPU > 70% (lab runs are CPU-bound and share the replica). Raise memory when working set > 75% under normal load, or OOM kills occur on large uploads.

### 10.2 Horizontal scaling rules

Because routes are synchronous and frequently wait on I/O, CPU is a poor scaling signal on its own. Scale on concurrent HTTP requests:

```bash
az containerapp update -n "$APP" -g "$RG" \
  --scale-rule-name http-concurrency --scale-rule-type http \
  --scale-rule-http-concurrency 30 --min-replicas 2 --max-replicas 10
```

Guidance for the concurrency value: about 75% of the request threads available per replica (`workers × 40 × 0.75`). With 1 worker that is 30.

Before raising `max-replicas`, recompute database connections (§10.3). Before running more than one replica at all, fix HZ-2/HZ-3 (rate limiting) and HZ-4 (startup migrations).

### 10.3 Uvicorn workers and threads

- Uvicorn reads `WEB_CONCURRENCY` for the number of worker processes (no image change needed):
  ```bash
  az containerapp update -n "$APP" -g "$RG" --set-env-vars WEB_CONCURRENCY=2
  ```
  Use 2 workers per vCPU at most. Each worker runs the startup lifespan (seed) and has its own rate-limit counters and DB pool.
- The thread pool per worker defaults to 40 (AnyIO). Raising it helps only when threads wait on I/O and the database has spare connections; it does not fix HZ-1. **[CODE CHANGE]** expose `THREADPOOL_SIZE` and set `anyio.to_thread.current_default_thread_limiter().total_tokens` at startup.

### 10.4 Database tuning

**Connection budget.** SQLAlchemy defaults are `pool_size=5`, `max_overflow=10` → up to **15 connections per worker process**.

```text
required = max_replicas × WEB_CONCURRENCY × 15  (+ migrations 1 + backup job 1 + ops sessions 5)
```

`required` must stay below `max_connections` minus the server's reserved connections. Burstable small SKUs have low limits (for example around 50), which 4 replicas with default pools can exhaust. Options, in order:
1. Choose a General Purpose SKU (D2ds_v5 or larger) for production.
2. Enable the built-in **PgBouncer** on Flexible Server (transaction pooling, port 6432) and point `DATABASE_URL` at port 6432:
   ```bash
   az postgres flexible-server parameter set -g "$RG" -s "$PG" --name pgbouncer.enabled --value true
   ```
   psycopg 3 with PgBouncer transaction mode requires server-side prepared statements to be disabled (`prepare_threshold=None`) **[CODE CHANGE: connect_args]**.
3. **[CODE CHANGE]** make `pool_size`/`max_overflow` configurable (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`) and set `pool_recycle=1800`, `pool_timeout=10`.

**Server parameters** (set with `az postgres flexible-server parameter set -g "$RG" -s "$PG" --name <n> --value <v>`):

| Parameter | Recommended | Why |
| --- | --- | --- |
| `log_min_duration_statement` | `500` (ms) | Log slow queries to Log Analytics |
| `azure.extensions` | include `PG_STAT_STATEMENTS` | Allow the extension |
| `shared_preload_libraries` | include `pg_stat_statements` (restart) | Enable statement stats; then `CREATE EXTENSION pg_stat_statements;` |
| `idle_in_transaction_session_timeout` | `60000` (ms) | Kill leaked transactions holding locks |
| `statement_timeout` | Set per role: `ALTER ROLE mentor_app SET statement_timeout = '15s';` | Bound runaway queries; migrations use a separate role without it |
| `lock_timeout` | Per migration session: `SET lock_timeout = '5s';` | Migrations fail fast instead of blocking traffic |
| `autovacuum_vacuum_scale_factor` | `0.05` on hot tables: `ALTER TABLE messages SET (autovacuum_vacuum_scale_factor = 0.05);` (also `xp_events`, `users`) | High insert/update churn (HZ-11 updates `users` on every request) |

**Indexes to verify exist** (they are defined in the models; confirm after each migration):

```sql
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public' AND tablename IN
('messages','xp_events','flashcards','quiz_results','code_submissions','research_documents','document_chunks','concept_mastery')
ORDER BY tablename;
```

Expected include: `ix_messages_conversation`, `ix_xp_events_user_created`, `ix_flashcards_due`, `ix_quiz_results_user`, `ix_code_submissions_user`, `ix_research_documents_user`, document_chunks by `document_id`. Leaderboard reads order users by XP; add `CREATE INDEX CONCURRENTLY ix_users_xp ON users (xp DESC);` when `users` exceeds ~50k rows and Q-DB8 shows the leaderboard query in the top 10.

### 10.5 Application-level tuning (code changes, prioritised)

| # | Change | Expected effect | Hazard |
| --- | --- | --- | --- |
| 1 | Explicit timeouts and ≤ 1 retry on model clients; reuse clients instead of constructing per call | Removes thread-pool exhaustion from slow providers; lowers latency | HZ-1 |
| 2 | Store chunk vectors (Qdrant) and query them; never re-embed chunks at query time | Research analysis from minutes to < 2 s; embedding cost per question from N calls to 1 | HZ-5 |
| 3 | Upsert user only when claims change (cache `clerk_id → user_id` for the token lifetime) | Removes one write per request | HZ-11 |
| 4 | Request-duration access log (JSON with route, status, ms, trace id) | Real latency SLOs | §5.4 |
| 5 | Shared rate limiter (Azure Cache for Redis) keyed by user id for authenticated routes and IP for anonymous | Correct limits across replicas | HZ-2/3 |
| 6 | Migrations as a separate job; seed only when catalog version changes | Safe scale-out and faster starts | HZ-4 |
| 7 | Background queue for ingestion | Uploads no longer hold request threads | HZ-13 |
| 8 | Streaming chat (SSE) | Time to first token instead of full-reply latency | SRS FR-TUT-001 |
| 9 | Cache `GET /learning-paths` and `/knowledge-graph` responses (in-process, 60 s; invalidated on deploy) | Fewer DB reads on hot catalog routes | — |
| 10 | Langfuse client created once; current SDK API | Working traces at negligible overhead | HZ-8 |

### 10.6 Model latency and cost tuning

- Keep `max_tokens` for tutor replies at the current 700 unless a prompt requires more; every extra 100 output tokens adds roughly 1–2 s on small models.
- Order providers by measured p95 latency and cost; the router tries OpenAI, then Anthropic, then Gemini, based on which keys exist. To change the order today, remove keys; **[CODE CHANGE]** make order configurable.
- Trim conversation history: the engine already limits to 20 prior turns; reduce if prompts approach model context or cost targets.
- Watch the curriculum-fallback share: falling back is cheap and fast but lowers quality; it should be < 1% in normal operation.

### 10.7 Frontend tuning (Vercel)

- Monitor Core Web Vitals in Vercel Speed Insights: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at p75.
- Static marketing pages and the path catalogue should be statically rendered or ISR-cached.
- Heavy client libraries (Mermaid, KaTeX, Monaco, Cytoscape) must be dynamically imported only on pages that use them.
- `NEXT_PUBLIC_API_URL` should point to an API hostname in the same geography as most learners; add a CDN in front of the API only for cacheable `GET` catalogue routes.

### 10.8 Load testing

Before raising capacity or after major changes, run a load test in staging with production-like data:

- Tool: k6 or Locust, scripts stored in `ops/load/`.
- Mix (per minute per 100 virtual learners): 60% read (dashboard, paths, progress), 20% chat, 10% quiz generate/grade, 7% lab run, 2% flashcards, 1% research analyze.
- Ramp to 2× expected peak, hold 30 minutes.
- Pass: SLO latencies met, `5xx` < 0.5%, DB connections < 70%, no replica restarts.
- Use a staging-only model key with its own spend cap, or stub providers for capacity tests.

---

## 11. Recovery Procedures

### 11.1 Roll back an API deploy

Use multiple-revision mode so the previous revision stays available for instant rollback:

```bash
az containerapp revision set-mode -n "$APP" -g "$RG" --mode multiple
```

Rollback:

```bash
# 1. Find the last good revision
az containerapp revision list -n "$APP" -g "$RG" --query "[].{rev:name,created:properties.createdTime,active:properties.active,traffic:properties.trafficWeight,image:properties.template.containers[0].image}" -o table

# 2. Ensure it is active
az containerapp revision activate -n "$APP" -g "$RG" --revision <good-rev>

# 3. Shift all traffic to it
az containerapp ingress traffic set -n "$APP" -g "$RG" --revision-weight <good-rev>=100

# 4. Deactivate the bad revision once traffic is off it
az containerapp revision deactivate -n "$APP" -g "$RG" --revision <bad-rev>
```

**Schema caveat:** a rollback is safe only if the old code works with the current schema. Migrations must be backward-compatible for one release (expand → migrate → contract). If the bad release ran a non-backward-compatible migration, rolling back code alone will fail; options: fix forward, or PITR (§4.2) to before the migration (data loss window — IC decision).

Verify with the smoke test (§9.6) and watch §6.1 alerts for 15 minutes.

### 11.2 Restart replicas (stuck threads, memory growth)

```bash
az containerapp revision restart -n "$APP" -g "$RG" --revision <rev>
```

This restarts all replicas of the revision; with ≥ 2 replicas and readiness probes, Container Apps replaces them gradually. If only one replica exists, expect a brief interruption; scale to 2 first.

### 11.3 Roll back the studio (Vercel)

- Dashboard: Project → Deployments → previous production deployment → "Instant Rollback".
- CLI:
  ```bash
  vercel rollback <previous-deployment-url-or-id> --scope <team>
  ```
- Rollback restores the previous build's `NEXT_PUBLIC_*` values (they are compiled in). Environment variable changes require a **new** deployment to take effect.

### 11.4 Disable or switch a model provider (kill switch)

The router only tries providers whose key is set. Removing a key is the provider kill switch.

```bash
# Disable OpenAI (also switches embeddings to the local hash model)
az containerapp update -n "$APP" -g "$RG" --remove-env-vars OPENAI_API_KEY \
  --revision-suffix "no-openai-$(date -u +%H%M)"

# Re-enable later (secret 'openai-api-key' still exists in the app's secrets)
az containerapp update -n "$APP" -g "$RG" --set-env-vars OPENAI_API_KEY=secretref:openai-api-key \
  --revision-suffix "openai-$(date -u +%H%M)"
```

Effects to communicate:
- Removing all three keys → tutor answers from authored curriculum only (`/health` shows `llm: curriculum`); quizzes stay authored and graded deterministically; research analysis becomes extractive only.
- Removing OpenAI → embeddings use the hash model; documents remain analysable because analysis re-embeds both sides with the active model (HZ-5). Once vectors are persisted (HZ-5 fixed), switching embedding models will require re-indexing instead.

### 11.5 Recover from a failed migration

1. Traffic stays on the previous revision (multiple-revision mode, §11.1).
2. Inspect: `alembic current` in a replica of the failed revision, and `SELECT version_num FROM alembic_version;`.
3. PostgreSQL DDL is transactional, so a failed Alembic migration usually rolled back fully. Confirm by comparing the schema with the expected head (`\d <table>`).
4. If fully rolled back → fix the migration, release a new image.
5. If partially applied (non-transactional steps such as `CREATE INDEX CONCURRENTLY`) → complete or reverse the step manually per the migration author's notes, with an on-demand backup taken first.
6. If data was damaged → PITR to the pre-change backup time recorded in the change ticket (§4.2).

### 11.6 Database failover and server-level recovery

- **Zone-redundant HA failover** is automatic (typically 60–120 s). The API recovers via `pool_pre_ping`; if errors persist 5 minutes after the server reports `Ready`, restart replicas (§11.2).
- **Planned failover test** (quarterly, low traffic):
  ```bash
  az postgres flexible-server restart -g "$RG" -n "$PG" --failover Planned
  ```
- **Server unrecoverable or data corrupted** → PITR to a new server (§4.2).

### 11.7 Regional disaster recovery

Trigger: Azure declares a regional outage affecting Container Apps or PostgreSQL in the primary region, and the expected restoration exceeds 2 hours, or the IC decides based on impact.

**Targets:** RTO 4–8 hours, RPO up to the geo-backup lag (typically < 1 hour).

Pre-requisites (verify quarterly): geo-redundant PostgreSQL backups; IaC or documented CLI to create a Container Apps environment in the DR region; images in GHCR (global); secrets in a DR Key Vault or exported recovery procedure; DNS for `api.<domain>` with a TTL ≤ 300 s.

Procedure:
1. IC declares DR; Comms posts status (extended outage).
2. Geo-restore PostgreSQL into the DR region (§4.5). Apply server parameters and network rules.
3. Create the DR Container Apps environment and app with the **same image tag** as production:
   ```bash
   az containerapp env create -g "$RG-dr" -n "$ENVNAME-dr" -l northeurope
   az containerapp create -g "$RG-dr" -n "$APP-dr" --environment "$ENVNAME-dr" \
     --image "$IMAGE:<current-tag>" --target-port 8000 --ingress external \
     --min-replicas 1 --max-replicas 1 --cpu 1.0 --memory 2Gi \
     --secrets database-url="<dr-db-url>" clerk-webhook-secret=... stripe-secret-key=... stripe-webhook-secret=... openai-api-key=... \
     --env-vars APP_ENV=production DATABASE_URL=secretref:database-url CLERK_JWKS_URL=... CLERK_ISSUER=... \
       QDRANT_URL=... CORS_ORIGINS="$WEB_URL" OPENAI_API_KEY=secretref:openai-api-key FORWARDED_ALLOW_IPS="*"
   ```
   Start with 1 replica (migrations/seed, HZ-4), then scale to normal.
4. Smoke test against the DR FQDN.
5. Switch DNS for `api.<domain>` to the DR app (custom domain + managed certificate on the DR app first). If the studio uses the API FQDN directly in `NEXT_PUBLIC_API_URL`, update it in Vercel and redeploy.
6. Update Stripe and Clerk webhook endpoints if they point to a region-specific hostname (they should point to `api.<domain>`).
7. Monitor; reconcile writes lost in the geo-backup lag window (§4.8).
8. **Failback** after the primary region recovers: plan a maintenance window; dump/restore or PITR from the DR server back to primary; repeat cutover in reverse. Never run both regions writable at once.

### 11.8 Secret rotation (planned or emergency)

| Secret | Where to rotate | Learner impact |
| --- | --- | --- |
| `DATABASE_URL` password | `ALTER ROLE mentor_app PASSWORD '<new>';` then update secret | Brief, during revision roll |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | Provider console: create new key, deploy, then revoke old | None if done in order |
| `STRIPE_SECRET_KEY` | Stripe → Developers → API keys → roll key (optionally with expiry on old) | None if done in order |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Webhooks → endpoint → Roll secret (old secret can remain valid up to 24 h) | Webhooks fail if mismatched; resend afterwards |
| `CLERK_WEBHOOK_SECRET` | Clerk → Webhooks → endpoint → rotate signing secret | Replay failed messages after |
| `LANGFUSE_*` | Langfuse project settings | None |
| Clerk instance keys (JWKS) | Clerk-managed; if Clerk signing keys are rotated, JWKS updates automatically | Sessions may need re-login |

Procedure (zero-downtime for keys that allow overlap):

```bash
# 1. Store the new value in Key Vault (canonical copy)
az keyvault secret set --vault-name "$KV" --name openai-api-key --value "<new>"
# 2. Update the Container App secret
az containerapp secret set -n "$APP" -g "$RG" --secrets "openai-api-key=<new>"
# 3. Roll a new revision so replicas read it
az containerapp update -n "$APP" -g "$RG" --revision-suffix "rot$(date -u +%m%d%H%M)"
# 4. Smoke test (§9.6), then revoke the old key at the provider
```

**Emergency rotation (suspected leak):** revoke the old key **first** at the provider (accept brief failover or degradation), then deploy the new key. Search logs and the repository for the leaked value; if it was committed to Git, rotate regardless of history rewriting and notify Security.

### 11.9 Learner data requests during operations

Until account deletion and export are implemented in the product (SRS FR-ACC-007/008; HZ-14), Support escalates verified requests to the Backend lead, who runs a reviewed script in a transaction: delete the user row (cascades to conversations, messages, quizzes, results, submissions, documents, chunks, embeddings, plans, flashcards, reviews, mastery, progress, achievements, XP events), delete the user in Clerk, and anonymise Stripe customer metadata. Record completion date without personal data. Deadline: 30 days from verified request.

### 11.10 After any recovery

1. Smoke test passes (§9.6).
2. Alerts quiet for 30 minutes.
3. Backups resume on the (possibly new) server; take an on-demand backup immediately after any cutover.
4. Update the infrastructure record (server names, revision names, DNS) in the ops repository.
5. Close the incident; schedule the postmortem.

---

## 12. Emergency Contacts Structure

Keep the live roster in the paging tool and the password manager. This section defines the **structure**; fill names and numbers in the secured copy, not in Git.

### 12.1 Internal roster

| Role | Primary | Secondary | Phone (24×7) | Chat handle | Hours | Authority |
| --- | --- | --- | --- | --- | --- | --- |
| On-call primary (Ops) | Weekly rotation | — | Paging tool | `@oncall-primary` | 24×7 | Run all runbook procedures; rollbacks; restarts; scale |
| On-call secondary | Weekly rotation | — | Paging tool | `@oncall-secondary` | 24×7 | Incident Commander for SEV1/SEV2 |
| Engineering lead | <name> | <deputy> | <number> | | 24×7 for SEV1 | Approves destructive actions, DR, deploy freezes |
| Backend lead | <name> | <deputy> | <number> | | Business hours; SEV1 on call | API, database, Clerk, Stripe integration |
| Frontend lead | <name> | <deputy> | <number> | | Business hours | Studio, Vercel |
| AI lead | <name> | <deputy> | <number> | | Business hours; SEV2+ | Providers, prompts, model quality, spend |
| Security lead | <name> | <deputy> | <number> | | 24×7 for security incidents | Co-IC for security; secret rotation; evidence |
| DPO / Legal | <name> | External counsel | <number> | | 24×7 reachability for breaches | Regulatory notifications (72 h) |
| Product / Communications | <name> | Support lead | <number> | | Business hours; SEV1 24×7 | Status page, learner messaging |
| Finance | <name> | — | <number> | | Business hours | Stripe disputes, provider billing limits |
| Head of Engineering / CTO | <name> | — | <number> | | SEV1 > 60 min | Executive decisions, external statements |

### 12.2 On-call rules

- Rotation: weekly, Monday 09:00 local time handover with a written handover note (open incidents, ongoing risks, silenced alerts).
- Primary acknowledges pages within 5 minutes (SEV1) or 15 minutes (SEV2); escalation in §2.1 is automatic.
- On-call engineers must have: laptop, Azure CLI logged in with PIM eligibility, VPN/network access to the database (if private), access to Vercel, Stripe (read), Clerk (read), provider consoles (read), the paging tool, and this runbook offline.
- Compensation and time-off-in-lieu per HR policy after out-of-hours pages.

### 12.3 Vendor and status contacts

| Vendor | Status page | Support channel | Account id / plan (secured copy) |
| --- | --- | --- | --- |
| Microsoft Azure | https://azure.status.microsoft/status (and Azure Service Health in the portal for our subscriptions) | Azure Portal support request | Subscription id; support plan |
| Vercel | https://www.vercel-status.com | Dashboard support | Team id; plan |
| Clerk | https://status.clerk.com | Dashboard support | Instance id |
| Stripe | https://status.stripe.com | Dashboard support | Account id |
| OpenAI | https://status.openai.com | Platform help center | Org id |
| Anthropic | https://status.anthropic.com | Console support | Org id |
| Google (Gemini API) | https://aistudio.google.com/status | Google Cloud / AI Studio support | Project id |
| Qdrant | Vendor status page (record URL in secured copy) | Qdrant Cloud support | Cluster id |
| GitHub (GHCR, Actions) | https://www.githubstatus.com | support.github.com | Org |
| Langfuse | Vendor status page (record URL) | Support email | Project id |
| Email provider (when selected) | Vendor status page | Support | Account |

Subscribe the ops channel to every status page's notifications (RSS, email, or chat integration).

### 12.4 Regulatory contacts (used only by DPO/Legal)

| Authority | Jurisdiction | When |
| --- | --- | --- |
| Lead EU supervisory authority (determined by EU establishment; e.g. CNIL for France, AEPD for Spain) | EU learners | Personal-data breach likely to result in risk, within 72 h |
| UK Information Commissioner's Office (ICO) | UK learners | Same |
| Nigeria Data Protection Commission (NDPC) | Nigerian learners | Same (NDPA 2023) |
| California Attorney General (if thresholds met) | California residents | Per CCPA/CPRA breach rules |

### 12.5 Contact verification

- Monthly: send a test page to each on-call engineer; confirm acknowledgement.
- Quarterly: verify every phone number, vendor account access, and support plan level; update the secured roster and note the verification date.

---

## Appendix A — Standard release and rollback

1. **Pre-release (change ticket):** CI green on the commit; migration reviewed for backward compatibility (expand/contract); on-demand PostgreSQL backup taken and its UTC time recorded (§3.2); release window outside peak (avoid 17:00–22:00 in main learner time zones); on-call aware.
2. **Build:** tag `vX.Y.Z` → `publish` workflow pushes `ghcr.io/<owner>/<repo>/api:vX.Y.Z`. Confirm the image exists.
3. **Deploy to staging** with the same tag; run the smoke test.
4. **Deploy to production** as a new revision with 0% traffic (multiple-revision mode):
   ```bash
   az containerapp update -n "$APP" -g "$RG" --image "$IMAGE:vX.Y.Z" --revision-suffix "vXYZ"
   az containerapp ingress traffic set -n "$APP" -g "$RG" --revision-weight <current-rev>=100 "$APP--vXYZ"=0
   ```
   Note: the new revision's replicas run `alembic upgrade head` when they start; the migration therefore applies before traffic shifts. This is why migrations must be backward-compatible with the current revision.
5. **Verify the new revision** directly via its revision FQDN (`az containerapp revision show ... --query properties.fqdn`) with the smoke test.
6. **Shift traffic** 10% → watch 10 minutes → 50% → watch 10 minutes → 100%:
   ```bash
   az containerapp ingress traffic set -n "$APP" -g "$RG" --revision-weight <current-rev>=90 "$APP--vXYZ"=10
   ```
7. **Watch** §6.1 alerts for 30 minutes after 100%.
8. **Keep** the previous revision active (0% traffic) for 24 hours for instant rollback (§11.1), then deactivate.
9. **Studio:** Vercel production deploys from the main branch; promote only after the API is at 100% if the studio depends on new API fields.

## Appendix B — Communication templates

**B.1 Internal declaration**

```text
:rotating_light: INCIDENT DECLARED — SEV<1|2|3> — <short title>
Impact: <who/what is affected, e.g. "Tutor replies failing for all learners">
Started: <UTC time> (detected <UTC time> via <alert/report>)
IC: @<name>  Ops: @<name>  Comms: @<name>  Scribe: @<name>
Bridge: <link>
Current status: Investigating. Next update at <UTC time>.
```

**B.2 Status page — investigating**

```text
Title: Some learners can't <use the tutor / sign in / complete payments>
We're investigating reports that <plain description>. Your progress, XP, and streaks are safe.
We'll post an update within <30|60> minutes.
```

**B.3 Status page — identified / monitoring**

```text
We've identified the cause (<plain, non-technical summary>) and applied a fix.
<Feature> is working again for most learners. We're monitoring closely.
```

**B.4 Status page — resolved**

```text
This incident is resolved. Between <UTC start> and <UTC end>, <impact>.
<If streaks/XP were affected: "We've restored any streaks interrupted during this period.">
We're sorry for the disruption. A summary of what happened and what we're changing will follow.
```

**B.5 Streak protection note** — when an outage longer than 2 hours overlaps a learner day, the Backend lead runs a reviewed script to preserve streaks for learners active the previous day (set `last_active_on` to the outage date for those users). Announce it in the resolution update.

## Appendix C — Postmortem template

```markdown
# Postmortem: <title> (<INC id>, SEV<n>)

Date: <UTC date>   Authors: <names>   Status: Draft | Reviewed

## Summary
Two or three sentences: what happened, impact, duration, how it was resolved.

## Impact
- Learners affected (count or %), features affected, duration (UTC start → end)
- Data impact (none / lost writes window / exposure — details)
- Error budget consumed
- Financial impact (refunds, provider spend)

## Timeline (UTC)
| Time | Event |
| --- | --- |

## Root cause
What in the system allowed this to happen. Link to code, configuration, or hazard IDs (HZ-n).

## Detection
How we found out. Time to detect. Could an alert have caught it sooner?

## Response
What worked, what slowed us down. Which runbook sections were used; were they correct?

## Action items
| # | Action | Type (prevent/detect/mitigate/process) | Owner | Due | Ticket |
| --- | --- | --- | --- | --- | --- |

## Lessons
What we learned that is not captured as an action item.
```
