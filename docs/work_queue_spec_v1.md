# Work Queue Spec v1 (Factory v1.5.0)
# SSOT – Authoritative, Binding, Evidence-Based

## 0. Scope / Binding

This document defines the only allowed design and behavior for the Factory Work Queue
for v1.5.0 (Factory-Level, Minimal).

Anything not explicitly allowed here:
- MUST NOT be implemented
- MUST NOT be proposed beyond design notes
- MUST NOT be executed in automation

This spec is binding for:
- Humans
- GPT Projects
- VS Code / Copilot Agent mode
- GitHub Actions-based automation

---

## 1. Purpose

Provide a single, auditable, FIFO work queue so that:
- Factory work is serialized (no parallel execution hazards)
- A single job runs at a time
- Human-triggered enqueue is the only way to add new jobs
- Worker execution can safely stop (blocked) without corrupting order

Non-goals (explicitly forbidden in v1.5.0):
- Parallel workers / concurrent job execution
- Automatic enqueue (event-driven auto-queueing)
- Priority / dynamic reordering
- Multi-repo orchestration
- AaaS-level isolation / ContextPackage wiring (v1.6.0)

---

## 2. SSOT Storage

### 2.1 Canonical Queue File (SSOT)

The queue SSOT is a JSONL file:

- Path: `factory/work_queue.jsonl`
- Format: JSON Lines (one JSON object per line)
- Semantics: Append-only event log (preferred), with derived "current state" per jobId.

Rationale:
- Minimal tooling
- Easy auditing via git history
- Avoids fragile YAML diffs for event streams

### 2.2 Where the SSOT Lives (Branch Policy)

To keep `main` protected and avoid “state churn” PRs:
- SSOT branch SHOULD be a dedicated branch, e.g. `__factory_state__/work_queue`.

Rules:
- Human enqueue MUST be performed by a human action (CLI/manual), targeting the SSOT branch.
- Worker state updates MAY write to the SSOT branch (no PR required), because it is operational state.
- Product/feature code changes MUST still follow the Human Gate policy on `main`.

This spec does not mandate GitHub branch protection settings,
but mandates the behavioral rules above.

---

## 3. Data Model

Each line is an "event" with required keys.

### 3.1 Event Schema (Required)

- `eventId` (string, unique)
- `ts` (RFC3339 UTC string, e.g. `2026-01-10T06:33:58Z`)
- `actor` (string, GitHub login or “github-actions[bot]”)
- `type` (string enum): `enqueue | start | block | unblock | done | fail | cancel`
- `jobId` (string, stable job identity)
- `job` (object, REQUIRED only for `enqueue`):
  - `kind` (string enum): `open_pr | release | changelog | maintenance`
  - `repo` (string, `owner/name`)
  - `base` (string, base branch, e.g. `main`)
  - `payload` (object, arbitrary but stable; must be JSON-serializable)

Optional keys:
- `evidence` (object): `{"url": "...", "sha": "...", "runId": "..."}`
- `reason` (string): reason for block/fail/cancel
- `meta` (object): any extra stable metadata (must not include secrets)

### 3.2 Derived Job State

The “current state” of a job is derived by folding events by `jobId` in file order.

Terminal:
- `done`, `fail`, `cancel`

Non-terminal:
- `queued` (after `enqueue` and before terminal)
- `running` (after `start` and before terminal)
- `blocked` (after `block` and before `unblock`/terminal)

---

## 4. FIFO Semantics (Hard Invariants)

These invariants MUST always hold:

1) FIFO order is defined by the first `enqueue` event order.
2) Worker MUST NOT start any job unless it is the earliest non-terminal job in the queue.
3) If the earliest non-terminal job is `blocked`, worker MUST stop and start nothing.
4) At most one job may be in `running` at any time.
5) Enqueue MUST be human-triggered.
6) Worker MUST be single-executor (no parallel workers in v1.5.0).

---

## 5. Concurrency / Locking

### 5.1 Queue Lock (Mandatory)

Queue read-modify-append MUST be guarded by a queue-level lock.

Recommended mechanism:
- Reuse RepoLock with a distinct lock namespace, e.g.
  - `refs/heads/__factory_lock__/work_queue/<epoch>`

Rules:
- Acquire queue lock before:
  - reading queue file
  - appending any event lines
- Release queue lock after the append is confirmed

### 5.2 RepoLock / PRSchedule (Still Applies)

For jobs that operate on a target repo:
- RepoLock MUST be acquired for write operations on that repo
- PRSchedule MUST be checked before any write operations

Work Queue does not replace those guards; it composes them.

---

## 6. Operations

### 6.1 Enqueue (Human Only)

Operation:
- Append an `enqueue` event.
- Human actor is required.

Validation:
- Must include `job.kind`, `job.repo`, `job.base`, `job.payload`.

No auto-enqueue. No implicit enqueue on merge.

### 6.2 Start (Worker)

Operation:
- Determine earliest non-terminal job.
- If blocked: exit with “blocked” (no changes).
- If queued: append `start` event, then execute job.

Validation:
- Must ensure no other job is running.
- Must ensure started job is the earliest non-terminal job.

### 6.3 Block / Unblock

Block:
- Worker may append `block` if it cannot proceed safely
  (e.g. PRSchedule indicates review is pending).

Unblock:
- MUST be human-triggered (v1.5.0).
- Append `unblock` event to the same jobId.

### 6.4 Done / Fail / Cancel

Done:
- Append `done` with evidence.

Fail:
- Append `fail` with reason and evidence.

Cancel:
- Human-triggered only; append `cancel`.

---

## 7. Error Policy

Fail-safe (prefer BLOCK):
- transient GitHub API failures (>=500, timeouts)
- temporary inability to fetch state
- “review required” conditions

Fail-fast (FAIL):
- invalid event schema
- invariant violation (e.g. attempt to start non-head job)
- lock acquisition failure (queue lock)

---

## 8. Example JSONL Lines

### Enqueue
{"eventId":"evt_0001","ts":"2026-01-10T06:40:00Z","actor":"milechy","type":"enqueue","jobId":"job_0001","job":{"kind":"open_pr","repo":"milechy/Hetzner_AaaS_Factory","base":"main","payload":{"proposalId":"p_123","title":"..."}}}

### Start
{"eventId":"evt_0002","ts":"2026-01-10T06:41:00Z","actor":"github-actions[bot]","type":"start","jobId":"job_0001","evidence":{"runId":"123456"}}

### Block (review required)
{"eventId":"evt_0003","ts":"2026-01-10T06:41:30Z","actor":"github-actions[bot]","type":"block","jobId":"job_0001","reason":"review_required","evidence":{"url":"https://github.com/.../pull/42"}}

### Unblock (human)
{"eventId":"evt_0004","ts":"2026-01-10T07:10:00Z","actor":"milechy","type":"unblock","jobId":"job_0001","reason":"approved"}

### Done
{"eventId":"evt_0005","ts":"2026-01-10T07:12:00Z","actor":"github-actions[bot]","type":"done","jobId":"job_0001","evidence":{"url":"https://github.com/.../pull/42","sha":"abc123"}}

---

## 9. Exit Criteria (v1.5.0)

- SSOT exists as JSONL event log: `factory/work_queue.jsonl`
- Enqueue is human-only, FIFO is enforced
- Only head-of-queue can run; blocked head stops execution
- At most one running job
- Queue lock prevents concurrent queue mutation
- Unit tests cover:
  - FIFO enforcement
  - blocked head stops worker
  - single-running invariant
  - enqueue requires human actor (policy enforced at CLI/API level)

# END