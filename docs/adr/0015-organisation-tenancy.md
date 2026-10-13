# ADR 0015 — Organisation tenancy and org-unit hierarchy

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13

## Context

The v1 data model has one implicit tenant. Every row belongs to a user or to the platform. The target schema in ADR 0011 adds row-level security keyed on `app.current_user_id`, but nothing keyed on an organisation.

The v2 direction sells to universities, schools, enterprises, bootcamps, and governments, while keeping self-registered learners. Institutions need campuses, departments, and cohorts; their own branding, SSO, and policies; and a guarantee that their learners' records are not visible to another institution. Adding a tenant column after data exists is the most expensive retrofit in the plan, which is why R1 includes it.

## Problem

Choose what a tenant is, how organisations are structured inside, how tenant data is isolated, and how a request knows which tenant it acts in.

## Decision

**A tenant is an organisation** (`tenancy.organisations`), with `kind` in `consumer`, `university`, `college`, `school`, `enterprise`, `bootcamp`, `government`, `publisher`. B2C learners belong to one built-in consumer organisation (slug `ai-mentor-public`). There is no "no tenant" code path.

**Org units** form a tree in `tenancy.org_units`, with a materialised `ltree` path (`<org>.<campus>.<dept>.<cohort>`, labels are short ids):

| Level | Parent | Required |
| --- | --- | --- |
| Organisation | none | yes (root) |
| Campus | organisation | no |
| Department | organisation, campus, or one department (faculty then department; two levels maximum) | no |
| Cohort | organisation, campus, or department | no; a cohort row lives in `classroom.cohorts` and references its org unit |

A trigger rejects depth beyond these rules and keeps paths current on moves, following the pattern already used by `curriculum.taxonomy_nodes`. Role assignments at an org unit apply to every unit whose path is a descendant (`path <@ scope_path`).

**Isolation** is shared database, shared schema:

1. Every tenant-scoped row carries `tenant_id uuid NOT NULL` referencing `tenancy.organisations`. Composite indexes lead with `tenant_id` where queries filter by tenant.
2. The API sets `app.tenant_id` with `SET LOCAL` in each transaction, beside `app.current_user_id`. RLS policies on tenant-scoped tables require `tenant_id = current_setting('app.tenant_id')::uuid` **and** the existing per-user policies from ADR 0011.
3. Person-level rows that follow a personal account across tenants (XP ledger, mastery evidence) carry the `tenant_id` of the context they were earned in; visibility to an organisation is decided by [ADR 0021](0021-learner-record-ownership.md). The current-state row `learning.concept_mastery` is one per person and concept and has no `tenant_id`; organisations see it only through consented, evidence-based views.
4. Platform staff act in the `platform` context, which sets no `app.tenant_id`. Platform reads of tenant data use the `mentor_platform` login role, which does **not** have `BYPASSRLS`: a handler under `/api/v1/platform/*` records a reason in `audit.data_access_log` and sets `app.access_reason_id`, and RLS policies admit platform reads only when that reason is present. Learner-private tables (`chat.*`, personal assets, document analyses) have no platform read policy; moderation uses a redacted view. `BYPASSRLS` is held only by the migration owner role ([07-database-design.md](../platform/07-database-design.md)).

**Active tenant context.** A request acts in exactly one tenant. Apps send it as `X-Org-Id` on `/learn` and `/me` calls and as the path parameter on `/orgs/{org_id}` calls. The API validates it against an `active` membership, and rejects a header and path that disagree with 400. A missing header on `/learn` defaults to the person's home tenant.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Schema per tenant | Thousands of schemas multiply migrations, connection search paths, and catalogue bloat. Cross-tenant platform analytics needs unions across schemas. |
| Database per tenant now | Strongest isolation and simplest residency story, but each tenant needs its own migrations, backups, and pool. Kept as an enterprise option (see Future considerations). |
| Tenancy in the application layer only | One missing `WHERE tenant_id` leaks data. RLS is a second fence that does not depend on every query being correct. |
| Clerk Organizations as the tenant model | Clerk holds identity, not authorisation or the org-unit tree. Campuses, departments, and cohorts do not fit its flat model ([ADR 0016](0016-scoped-rbac-abac.md)). |
| Adjacency list only, recursive CTEs for subtree checks | Every permission check on a cohort would walk the tree. `ltree` gives an indexed ancestor test. |

## Trade-off analysis

Shared schema is the cheapest to operate and the easiest to get wrong. RLS makes a wrong query return nothing rather than another tenant's rows; the cost is that every pooled connection must have `app.tenant_id` set inside the transaction, which ADR 0011 already requires for PgBouncer transaction mode.

Large tenants share capacity with small ones. Query plans lead with `tenant_id`, and noisy-neighbour limits are enforced per tenant at the API rate limiter. If a single tenant exceeds about 20 percent of total load, that is an extraction signal.

## Consequences

- R1 adds `tenant_id` to every tenant-scoped table and backfills it with the consumer organisation id. `identity.users` gains `account_type` and `home_tenant_id`.
- Integration tests run every RLS-protected query as two tenants and assert no cross-tenant rows.
- `tenancy.memberships` has status `invited`, `active`, `suspended`, `left`; only `active` memberships open a tenant context.
- Domain events carry `tenantid` ([ADR 0018](0018-event-outbox.md)).

## Future considerations

- Data residency (R4) uses regional deployment stamps: a full copy of the API, database, Qdrant, and storage in a region (for example EU and US), each holding only its tenants. A global directory maps organisation to stamp. Personal accounts stay in the home stamp.
- Database per tenant for a contract that requires it, using the same schema and the stamp mechanism with one tenant per database.
- Citus distribution on `tenant_id` if one PostgreSQL primary stops being enough.
