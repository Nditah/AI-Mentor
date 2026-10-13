# Security

## Access

Clerk verifies the person. Postgres stores the role. Admin routes require `admin`. Analytics require `instructor` or `admin`. The last admin cannot be demoted. Dev auth exists only when `APP_ENV` is `development` or `test`, and the header cannot grant a role.

Leaderboards expose display name, XP, level, and streak. They do not expose email.

Documents, conversations, quizzes, cards, and submissions are loaded with the current user id in the query.

## Input

Pydantic limits lengths on every body. Prompt text is screened. A message that is only an injection attempt is rejected. A lesson question that mentions injection in passing is flagged and still allowed, because students ask about the topic.

Untrusted document text is fenced before it is placed beside instructions. The security prompt in `backend/app/prompts/security.md` is composed into model calls.

## RAG

Chunk labels are the only citations a critique may use. If the model does not cite a supplied label, critique, gaps, and future work are dropped. Extractive mode never invents them. Embeddings from a failed provider call are not mixed with the hash space: if an API key is set and the call fails, embed raises.

## Code

The lab rejects the source before it runs, then runs `python -I` with a short timeout and truncated output. Chat does not execute code. Research chat does not analyze a paper that was not uploaded.

## OWASP

| Risk | Control in this build |
| --- | --- |
| Broken access control | Role checks, user-scoped queries, last-admin guard |
| Cryptographic failures | Clerk RS256 via JWKS; no homegrown passwords |
| Injection | Parameterized SQLAlchemy queries; prompt screening; fenced documents |
| Insecure design | No answer keys in quiz payloads; no invented paper critiques |
| Security misconfiguration | Production validator; security headers; powered-by header off |
| Vulnerable components | Pinned install via pyproject and package-lock; CI lint and test |
| Auth failures | JWT verification; dev auth cannot ship in production |
| Integrity | Stripe and Clerk webhooks verify signatures |
| Logging | Request failures are logged; secrets are not written into prompts on purpose |
| SSRF | The API does not fetch arbitrary URLs from learner input |

Rate limits are per process: 60 requests a minute, 20 on AI routes. Health, docs, and OPTIONS are exempt. This is not a cluster-wide limit.

Checkout and webhooks are the payment and identity edges. User deletion from a Clerk webhook is not implemented; treat that as an open item before a public launch.
