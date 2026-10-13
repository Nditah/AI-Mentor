# ADR 0026 — Interoperability standards: SSO, SCIM, LTI 1.3, OneRoster, xAPI

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13

## Context

v1 has Clerk social and email sign-in and nothing else. ADR 0005 notes staff SSO "through Clerk enterprise or a separate Entra tenant" as a future option.

Institutions already run an identity provider (Entra ID, Google Workspace, Okta, Shibboleth), a learning management system (Canvas, Moodle, Blackboard, Brightspace), and a student information system. They will not maintain accounts, rosters, or gradebooks twice. Procurement checklists ask for named standards by version.

## Problem

Choose which standards AI Mentor supports, which role it plays in each (provider or consumer), and in which release.

## Decision

The `integration` module ([ADR 0017](0017-bounded-contexts-platform-services.md)) owns the standards endpoints, except SSO, which `identity` owns.

| Standard | AI Mentor role | Endpoints or mechanism | Release |
| --- | --- | --- | --- |
| SAML 2.0 and OIDC SSO | Service provider, through Clerk enterprise connections | Configured per organisation in the Institution App (`tenancy.sso_connection:configure`); stored in `tenancy.sso_connections` with verified email domains (`tenancy.domains`) | R3 |
| SCIM 2.0 | Service provider (AI Mentor implements the SCIM server) | `/scim/v2/Users`, `/scim/v2/Groups`, `/scim/v2/ServiceProviderConfig`, bearer token per `integration.scim_clients` | R4 |
| LTI 1.3 Advantage | Tool | `/lti/login` (OIDC initiation), `/lti/launch`, `/lti/jwks`; Deep Linking 2.0, Assignment and Grade Services 2.0, Names and Role Provisioning Services 2.0 | R4 |
| OneRoster 1.2 | Consumer of rostering (REST pull, CSV import) | Scheduled sync per `integration.oneroster_syncs` | R4 |
| xAPI 1.0.3 and cmi5 | Activity provider; exports statements to the organisation's LRS | Worker consumer of domain events writes statements; `integration.xapi_exports` tracks endpoints and cursors | R4 |
| Open Badges 3.0 | Issuer | Signed credentials in the learning passport ([ADR 0021](0021-learner-record-ownership.md)) | R3 |
| QTI 3.0 | Import and export of assessment items | Content Studio import job and export download | R4 or later |

**SSO and provisioning rules.**

1. An SSO connection is bound to one organisation and its verified domains. A person signing in with a verified domain is routed to that connection.
2. Just-in-time provisioning creates a `managed` account and an `active` membership on first SSO sign-in, with the `learner` role unless the IdP group mapping says otherwise. Group-to-role mappings are configured by `org_admin` and may grant only organisation-scope roles below `org_owner`.
3. SCIM is authoritative when enabled: SCIM deactivation suspends the membership within 60 seconds; JIT does not override SCIM attributes.
4. Clerk remains the identity layer; AI Mentor stores its own mapping from IdP subject to person and never takes roles from SAML or OIDC claims except through the configured group mapping, evaluated server-side.

**LTI rules.**

1. A registration (`integration.lti_platforms`, `lti_deployments`) belongs to one organisation. A launch creates or matches a membership in that organisation and a cohort for the LMS context.
2. Deep linking returns links to courses, modules, or assignments from releases the organisation is licensed for.
3. Grades flow back through AGS only after release ([ADR 0025](0025-assessment-platform.md)). Line items are recorded in `integration.lti_line_items`.
4. Launches inside an LMS iframe do not rely on third-party cookies: the launch exchanges the LTI token for a short-lived AI Mentor session token held in memory, or opens a new window when the LMS allows it.

**xAPI rules.** Statements use pseudonymous actor accounts (`account.homePage` set to the organisation's AI Mentor URL, `account.name` set to the person id), never email, unless the organisation's DPA allows mbox.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Build SAML and OIDC in-house | Clerk enterprise connections already handle metadata, certificates, and IdP quirks; a second identity path would duplicate session handling. |
| LTI 1.1 | Deprecated by 1EdTech; OAuth 1.0 signatures and no grade services comparable to AGS. |
| Rely on CSV import only | Rosters drift within days; institutions expect SCIM or OneRoster. |
| SCORM packages | Packages content for an LMS to host; AI Mentor's tutor and adaptivity need the learner on the platform. cmi5 covers launch from an LMS with xAPI. |
| Custom REST rostering API only | Every institution would build a custom integration; standards make it configuration. |

## Trade-off analysis

Each standard adds certification and conformance testing work (1EdTech certification for LTI Advantage and OneRoster). Standards are scheduled by release so the Instructor and Institution Apps launch with SSO and badges first, and LMS integration follows once pilots confirm which LMSs matter.

Depending on Clerk enterprise connections ties SSO pricing and features to Clerk. If a contract needs an IdP Clerk cannot support, a dedicated broker is the fallback, still issuing Clerk sessions.

## Consequences

- `/lti/*` and `/scim/v2/*` sit outside `/api/v1` and authenticate with their own protocols; they do not accept Clerk session tokens.
- Integration events and failures appear in the Institution App's integration health page and in `audit`.
- [08-api-specification.md](../platform/08-api-specification.md) defines the endpoint contracts.

## Future considerations

- LTI Proctoring Services and Caliper Analytics if institutions require them.
- Ed-Fi for US K-12 rostering.
