# ADR 0016 — Scoped RBAC with ABAC policy evaluation

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13
- Amends: [ADR 0005](0005-clerk-authentication.md) (roles stay in Postgres, but `users.role` is replaced); replaces the linear role rank in `backend/app/domain/access.py`

## Context

`access.py` ranks three roles (`student` 1, `instructor` 2, `admin` 3) and answers one question: is the caller's rank at least the minimum? That cannot express "instructor of this cohort but not that one", "reviewer who did not author this draft", "org admin of university A and learner in the consumer organisation", or "no tutor solutions while this exam is open".

[docs/platform/README.md](../platform/README.md) defines 22 human role IDs plus `system`, five org-unit scope types plus `workspace`, a permission format, and the attribute set the policy engine evaluates.

## Problem

Choose how roles are assigned, how permissions are named and checked, where attribute conditions live, and how decisions are recorded, without slowing every request or depending on a vendor for authorisation.

## Decision

**Role assignments.** A role assignment is (person, role, scope) in `authz.role_assignments`, with `scope_type` in `platform`, `organisation`, `campus`, `department`, `cohort`, `workspace`, a `scope_id`, the scope's `ltree` path, `granted_by`, and optional `expires_at`. A person may hold many. Roles and their permissions are seeded data in `authz.roles`, `authz.permissions`, and `authz.role_permissions`. Organisations cannot create roles in R1–R3.

**Permissions** use `<context>.<resource>:<action>` in lower snake case, for example `assessment.grade:override`. The context is a bounded-context module name ([ADR 0017](0017-bounded-contexts-platform-services.md)).

**Decision rule.** Allow when a role assignment grants the permission, its scope contains the target resource (`resource_path <@ scope_path`, or same workspace), and every applicable condition passes. Deny by default. Explicit deny policies win over any allow.

**Policy engine.** An in-process package `backend/app/domain/authz` with no FastAPI or SQLAlchemy imports:

| Part | Responsibility |
| --- | --- |
| `Subject`, `Resource`, `Context` | Typed attribute bags built by the API layer from the token, the loaded row, and request state |
| Policies | Declarative Python data: permission, effect (`allow` or `deny`), and conditions written as small composable predicates (`same_tenant`, `is_cohort_staff`, `not_author`, `mfa_within(minutes=15)`, `app_audience("admin")`, `integrity_mode_off`) |
| `authorize(subject, permission, resource, context) -> Decision` | Returns allow or deny, the matched assignment and policy ids, and a reason code |
| Organisation policy flags | Rows in `authz.policies` that switch built-in conditions per tenant (for example "grade overrides need lead instructor approval") |

Routers declare the permission with a dependency, `Depends(require("assessment.grade:override"))`, and pass the loaded resource. List endpoints push the scope filter into SQL so callers never receive rows they could not open one by one.

**Decision logging.** Denies for any permission, and allows for sensitive permissions (all `platform.*`, `audit.*`, `*.grade:override`, `*:publish`, role assignment, and platform reads of tenant data) are written to `authz.decision_log` with subject, permission, resource, decision, policy ids, and correlation id. Other allows are sampled at 1 percent.

**Identity versus authorisation.** Clerk proves who the person is and which app (`azp`) they are using. Clerk Organizations are not used for authorisation. Token claims never grant a role (carries forward SRS SEC-005; `azp` validation is SEC-002).

**Migration from v1** (expand, backfill, switch, contract):

| v1 `users.role` | v2 assignments |
| --- | --- |
| `student` | `learner` in the consumer organisation |
| `instructor` | `content_author` in `master`, plus `learner` in the consumer organisation |
| `admin` | `platform_admin`, plus `content_publisher` and `knowledge_steward` in `master`, plus `learner` in the consumer organisation |

`is_allowed(role, minimum)` remains as a shim mapping the old minimums to permissions until every router uses `require`. Then `users.role` and the rank are removed. The rule "the last admin cannot be demoted" becomes "the last `platform_admin`, and the last `org_owner` of each organisation, cannot be removed".

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Keep the rank and add more levels | A rank cannot express scope or relationships. "Instructor in cohort A" is not above or below "org admin of B". |
| Clerk Organizations roles | Flat per organisation, no campus, department, cohort, or workspace scope, and roles would live outside the database that RLS and audit use. ADR 0005 already rejected roles in Clerk metadata. |
| OPA or Cedar as a sidecar service now | A network hop or WASM runtime on every request, a second language for policies, and data synchronisation into the engine. The current rule set fits in Python with unit tests. |
| Pure ABAC with no roles | Hard for institution admins to reason about and to audit. Roles give the RBAC matrix a stable shape; attributes refine it. |
| Relationship-based (Zanzibar-style) store | Strong for sharing graphs. AI Mentor's relationships are few and live in the same tables (cohort staff, authorship). |

## Trade-off analysis

An in-process engine is fast (assignments for a person are cached per request) and testable as pure functions, at the cost of being Python-only. Policies are data structured like Cedar statements (principal, action, resource, conditions) so a later move to Cedar is a translation.

Decision logging of every allow would write more rows than chat. Sampling non-sensitive allows keeps the log useful for audits without becoming the largest table.

## Consequences

- [10-rbac-matrix.md](../platform/10-rbac-matrix.md) is generated from the seeded role–permission data and checked in CI.
- Every new endpoint names a permission in review. A test enumerates routes and fails on any route without one, except the public allow-list.
- Role changes publish `authz.role_assignment.granted` and `authz.role_assignment.revoked` and invalidate the person's cached assignments.

## Future considerations

- Cedar (embedded) if organisations need custom roles or policy authoring (R4 or later).
- Time-boxed delegation (for example a TA granted `assessment.grade:release` for one assignment).
