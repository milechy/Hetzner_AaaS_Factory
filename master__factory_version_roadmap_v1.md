# Factory Version Roadmap v1
# SSOT – Authoritative, Binding, Evidence-Based

## 0. Purpose

This document defines the **only allowed development path** for the AaaS Factory
until it is considered **launch-ready**.

Anything not explicitly listed as "Allowed" for a given version:
- MUST NOT be implemented
- MUST NOT be proposed
- MUST NOT be discussed beyond design notes

This roadmap is binding for:
- Humans
- GPT Projects
- VS Code Agent / GitHub Copilot Agent mode

---

## 1. Definitions

### SSOT (Single Source of Truth)
This file is the **authoritative and binding** roadmap.
Any conflicting plan, note, or instruction is **invalid** unless it is merged into this file via PR.

### Launch-Ready Factory (Target)
A Factory is considered **launch-ready** when:

- Release Factory (tag → automated release) is stable
- Factory itself can be developed **semi-automatically**:
  - Task Brief → VS Code / Copilot → PR → Human Gate
- Minimum safety guards prevent concurrent corruption:
  - Repo-level locking
  - PR scheduling / review blocking

Parallel AaaS development and full Self-Dev autonomy are **explicitly out of scope**
for launch readiness.

---

## 2. Current State (Evidence-Based)

### Achieved
- v1.3.7
  - Fully automated Release Factory (L2)
  - CHANGELOG as sole release truth
  - Fail-Fast CI/CD
  - Open-PR + Human Gate enforced

### Not Implemented (as capabilities)
- Work Queue / Concurrency orchestration
- ContextPackage (AaaS-level isolation)
- PR scheduling / review blocking
- Runner separation (Hetzner / Mac)
- Self-Dev autonomous loops (L4)

> Note: “Not Implemented” means “not present as a supported, production-usable capability”.
> Experiments are prohibited unless explicitly Allowed in the version plan below.

---

## 3. Version-by-Version Roadmap (Binding)

### v1.3.8 — Documentation & State Alignment
Status: COMPLETE

Allowed:
- SSOT alignment
- README clarification
- Automation master normalization

Not Allowed:
- Any functional changes
- Any concurrency features

---

### v1.3.9 — RepoLock (Minimal Safety Guard)
Goal:
Prevent concurrent modifications to the same repository.

Allowed:
- Repo-level lock mechanism (file / label / branch / metadata based)
- Lock acquisition & release via PR lifecycle
- Lock state visibility (logs / labels)

Not Allowed:
- Work Queue
- Multi-repo orchestration
- Parallel AaaS development
- ContextPackage

Exit Criteria:
- Two simultaneous PR attempts cannot modify the same repo state

---

### v1.4.0 — PR Scheduling (Minimal)
Goal:
Ensure unreviewed PRs block subsequent automation.

Allowed:
- PR state inspection
- Automation pause when review is pending
- Single-active-PR policy per repo

Not Allowed:
- Priority queues
- Automatic PR merging (except the explicit changelog-only flow, if defined elsewhere)
- Multi-agent arbitration

Exit Criteria:
- Factory automation halts safely when PR awaits human review

---

### v1.5.0 — Work Queue (Factory-Level, Minimal)
Goal:
Serialize Factory work without parallel execution hazards.

Allowed:
- Single global work queue
- FIFO execution
- Explicit human-triggered enqueue

Not Allowed:
- Parallel execution
- Dynamic scaling
- AaaS-level queues

Exit Criteria:
- No two Factory jobs run concurrently

---

### v1.6.0 — ContextPackage (Design + Skeleton Only)
Goal:
Prepare for future parallel AaaS development without enabling it.

Allowed:
- ContextPackage specification
- Interfaces and data contracts
- No execution wiring

Not Allowed:
- Runtime isolation
- Concurrent execution
- Multi-AaaS runs

Exit Criteria:
- ContextPackage defined but unused

---

## 4. Explicitly Forbidden Until v2.x

- Parallel AaaS development
- Multi-repo concurrent execution
- Autonomous Self-Dev loops
- Agent-to-agent arbitration
- Memory layers spanning multiple runs

---

## 5. Change Policy

- This file may only be changed via PR
- Any change requires explicit human approval
- CHANGELOG entry is mandatory for version boundary changes

---

## 6. RepoLock TTL (Operational Default)
- Recommended ttl_seconds: 3600 (1 hour)
- Expired lock refs (now-epoch > ttl) may be reaped on acquire.
- Non-epoch refs are treated as active (do not reap).

#### Manual unlock (emergency)
List locks:
  gh api repos/:owner/:repo/git/matching-refs/heads/__factory_lock__/open_pr --jq '.[].ref'

Delete a lock ref:
  gh api -X DELETE repos/:owner/:repo/git/refs/heads/__factory_lock__/open_pr/<epoch>

---

### v1.7.0 — ContextPackage (SSOT Materialization, Minimal)
Goal:
Materialize a ContextPackage into SSOT **without enabling execution wiring**.

Allowed:
- Create ContextPackage SSOT artifacts on the `__factory_state__/contexts` branch
- Append-only / immutable context documents (create-only; no update/delete)
- Minimal CLI command to perform the materialization (no orchestration)
- RepoLock usage for contexts namespace (TTL default 3600)

Not Allowed:
- Any runtime isolation
- Any concurrent execution
- Any multi-AaaS runs
- Any automation wiring that triggers jobs using ContextPackage
- Any mutation of existing ContextPackage documents

Exit Criteria:
- A head-of-queue job can materialize exactly one ContextPackage into `__factory_state__/contexts`.
- Duplicate materialization for the same `jobId` is rejected.
- ContextPackage docs are created-only (immutable).

References:
- `master__context_package_spec_v1.md` §10A (v1.7.0 preview)
- `work_queue_operations_v1.md` (head-of-queue discipline)
- `factory_master_v3.md` (PR-first / no direct push)

---

# END