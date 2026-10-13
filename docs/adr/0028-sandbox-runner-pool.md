# ADR 0028 — Coding-lab runner: a gVisor or Firecracker pool we operate

- Status: Accepted
- Date: 2026-10-13
- Supersedes: SystemArchitecture ADR-07 (Azure Container Apps dynamic sessions)

## Context

The coding lab runs learner Python. Today that is a child `python -I` process inside the API container, behind an AST allow-list (`app/domain/sandbox.py`). A filter is not a boundary: SEC-01 showed an allowed module reaching `os` through a private attribute. Production therefore refuses `LAB_ENABLED=true`.

SRS SEC-051 requires an isolated, ephemeral container per run on a hardened runtime, naming gVisor `runsc` or Firecracker. The target system architecture proposed Azure Container Apps dynamic sessions (Hyper-V) instead, and TestPlan C-08 recorded the conflict.

## Problem

Choose the isolation runtime and who operates it, so the lab can be enabled in production without trusting the static filter.

## Decision

Learner code runs in a separate runner pool that the platform operates, never on API replicas.

- **Runtime.** gVisor `runsc` is the default: each run is a fresh container with a user-space kernel. Firecracker microVMs are the fallback if gVisor's syscall surface blocks a library the curriculum needs, or if a gVisor escape class is disclosed that Firecracker does not share.
- **Per run.** One ephemeral container per run, destroyed afterwards. Read-only root filesystem with a small `tmpfs`, non-root user, all capabilities dropped, seccomp default profile, `no-new-privileges`, PID, memory, and CPU limits, and a wall-clock timeout (3 s today, configurable up to SRS SEC-052's ceiling).
- **Network.** No egress. The pool sits in its own subnet with no route to PostgreSQL, Qdrant, Redis, Key Vault, or the API's subnet, and no managed identity.
- **Contract.** The API keeps the AST check as the first filter, then sends source and project id to the runner over an authenticated internal endpoint and receives stdout, stderr, exit status, and timing. Pass or fail is still decided by the API comparing expected output (BR-14).
- **Configuration.** `SANDBOX_RUNNER_URL` and a runner credential. Production refuses `LAB_ENABLED=true` unless the runner is configured; the local subprocess stays for development and tests only.
- **Region.** West Europe, beside the API (SRS CON-002).

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Azure Container Apps dynamic sessions | Managed Hyper-V isolation and no fleet to run, but it does not meet SEC-051 as written and would need a formal waiver (TestPlan C-08). The product owner chose to meet the SRS. |
| Keep the child interpreter with more filtering | A filter is not a boundary. SEC-01 is the evidence. |
| nsjail on the API hosts | Isolates processes, but untrusted code would still share a kernel and a host with the mentor and its secrets. |

## Trade-off analysis

Operating the pool costs the team node patching, gVisor upgrades, capacity planning, and an escape-test suite (TestPlan SEC-T-060…079). In return the isolation runtime is the one the SRS and the security review name, it can be tested in CI with Docker and `runsc`, and learner code never shares a kernel with the API.

gVisor adds per-syscall overhead. Lab runs are short and CPU-bound, so the cost is small. Firecracker gives a stronger hardware boundary at a higher start-up cost per run; it is the fallback, not the default.

## Consequences

- The lab stays off in production until the pool, its network isolation, and the escape suite pass a security review (Security-Compliance SEC-01 remains a launch blocker until then).
- Infrastructure needs a runner pool with gVisor installed. Whether that is an AKS node pool with a `runsc` RuntimeClass or a VM scale set running containerd with `runsc` is an implementation choice for the infrastructure owner.
- CI gains a job that runs the sandbox escape tests inside Docker with `--runtime=runsc`.
- Diagrams and text that showed ACA dynamic sessions now show the runner pool.
