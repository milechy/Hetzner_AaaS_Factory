# ContextPackage Spec v1
# SSOT – Authoritative, Binding, Design-Only

⚠️ DESIGN-ONLY SPEC — NO RUNTIME CODE, NO STORAGE, NO EXECUTION (v1.6.0)

Release Policy: This spec does NOT trigger a release by itself. No CHANGELOG entry is required unless behavior is implemented.

Normative language: The keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY** are used as binding requirements in this document.
Roadmap alignment: This spec is the v1.6.0 “design-only” deliverable referenced by `master__factory_version_roadmap_v1.md`.

## v1.7.0 Preview (Materialization Minimal)

This spec also defines the **minimum allowed v1.7.0 implementation boundary** for ContextPackage.

- v1.6.0 remains **design-only** (no runtime, no storage, no execution).
- v1.7.0 allows **minimal materialization** (SSOT write) while preserving **head-only** Work Queue execution.
- Any runtime behavior beyond what is explicitly allowed in the **v1.7.0** sections below is forbidden.

Status: **DESIGN ONLY (v1.6.0)**  
Scope: Humans / GPT Projects / VS Code Agent / Copilot Agent

This document is **authoritative and binding**.  
Anything not explicitly allowed here **MUST NOT be implemented**.

Design-only enforcement notes (v1.6.0):
- This spec MAY be referenced by humans/tools for documentation, review, and design validation.
- This spec MUST NOT be referenced by CI/workflows/automation to make execution decisions or to introduce any runtime behavior.

---

## 0. Purpose

The purpose of **ContextPackage** is to define a **stable, immutable execution context**
for a single Factory job.

In v1.6.0, ContextPackage is introduced as a **design artifact only**.

- It defines *what a job is allowed to see*
- It does NOT define *how a job is executed*
- It does NOT enable parallelism or isolation
- It MUST NOT be referenced by production code paths in v1.6.0

This specification exists to prevent accidental architectural drift
before concurrency is intentionally enabled.

---

## 1. Explicit Non-Goals (Hard Prohibitions)

The following are **explicitly forbidden in v1.6.0**:

- Runtime execution wiring (Worker / Queue / OpenPR integration)
- Container / VM / sandbox isolation
- Parallel job execution
- Multi-repo orchestration
- Secret storage or secret injection
- Cross-run or long-term memory layers
- Automatic ContextPackage creation at runtime
- (v1.6.0) Creating any ContextPackage SSOT branch or file
- (v1.7.0+) Any ContextPackage SSOT branch/file other than the explicitly allowed `__factory_state__/contexts` layout (see §10A)
- Importing ContextPackage types into runtime / production modules
- Adding tests that exercise ContextPackage behavior
- Referencing ContextPackage from CI, workflows, or automation code
- Any reference to ContextPackage in runtime logs (because ContextPackage MUST NOT be materialized in v1.6.0)
- Any generation of ContextPackage IDs in production/automation code paths
- Any CI job or GitHub Action step that reads/writes ContextPackage data

Any implementation of the above constitutes a **spec violation**.

---

## 2. Definitions

- **Job**: A Work Queue entry identified by `jobId`
- **ContextPackage**: Immutable description of a job’s execution context
- **Artifact**: A declared output reference (design only)
- **Actor**: Human or bot identity initiating an action
- **SSOT**: Single Source of Truth; binding and authoritative

---

## 3. ContextPackage Overview

- Exactly **one ContextPackage per job**
- ContextPackage is **immutable**
- ContextPackage is **pure data**
- ContextPackage is **not an execution environment**

In v1.6.0:
- ContextPackage MAY be defined
- ContextPackage MUST NOT be materialized or executed

---

## 4. Data Model (Normative)

### 4.1 Top-level Schema

```jsonc
{
  "contextId": "string",
  "jobId": "string",
  "repo": "owner/name",
  "base": "string",
  "actor": "string",
  "inputs": {},
  "lifecycle": {
    "state": "created",
    "createdAt": "RFC3339 (UTC, seconds precision)"
  },
  "artifacts": [],
  "limits": {},
  "meta": {}
}
```

### 4.2 Required Fields (MUST)

- contextId
- jobId
- repo
- base
- actor
- inputs
- lifecycle.state
- lifecycle.createdAt

### 4.3 Optional Fields (MAY)

- artifacts
- limits
- meta

### 4.4 Field Constraints

- repo: MUST be `owner/name`
- base: MUST be non-empty
- actor: MUST be a non-empty string
- inputs: MUST be a JSON object
- meta: MUST NOT contain secrets
- contextId: MUST be globally unique and immutable
- jobId: MUST reference an existing Work Queue jobId

---

## 5. ID and Timestamp Rules (Normative)

- contextId format: `ctx_<unix>_<rand4>`
  - Example: `ctx_1768109000_abcd`
- `<unix>`: epoch seconds
- `<rand4>`: 4-character lowercase hex suffix
- IDs are generated once and MUST be treated as immutable identifiers
- createdAt: RFC3339 UTC, seconds precision, MUST end with `Z`

---

## 6. Lifecycle Model (Design Only)

### 6.1 States (Conceptual)

- created
- running (future)
- done
- failed
- cancelled

### 6.2 Transition Rules

- In v1.6.0, lifecycle transitions are **conceptual only**
- No runtime transitions are allowed
- No state mutation is allowed

### 6.3 Prohibited Transitions (v1.6.0)

The following are explicitly prohibited in v1.6.0:

- Any runtime state transition (created → running/done/failed/cancelled)
- Any mutation of lifecycle.state after creation
- Any event emission tied to ContextPackage lifecycle

---

### 6.4 v1.6.0 Hard Constraints Summary

The following constraints are absolute for v1.6.0:

- ContextPackage exists only as a specification
- No code may create, store, mutate, or load ContextPackage
- No CLI, Worker, or Action may depend on ContextPackage
- ContextPackage MUST NOT appear in logs, branches, or artifacts

---

## 7. Relationship to Work Queue (Hard Boundary)

- Each jobId maps to exactly one contextId
- ContextPackage is conceptually defined at job start (no materialization)
- ContextPackage MUST NOT be created during enqueue
- v1.6.0 MUST NOT write ContextPackage to disk or branch
- v1.6.0 MUST NOT introduce any production code path dependency on ContextPackage
- v1.6.0 MUST remain fully compatible with v1.5.x Work Queue semantics without modification

```
WorkQueue jobId
      |
      | (conceptual start)
      v
ContextPackage contextId
```

---

## 8. Security and Data Handling

- ContextPackage MUST NOT store secrets
- Tokens and credentials MUST NOT be embedded
- Sensitive data MUST NOT be serialized
- In v1.6.0, ContextPackage MUST NOT appear in runtime logs because it MUST NOT be materialized.
- In future versions where ContextPackage is materialized, it SHOULD be safe to inspect/log *only if* it contains no secrets (per this spec).

---

## 9. Interfaces (Design Contracts Only)

### 9.1 Create (Design)

CreateContextPackage(job) -> ContextPackage

- No side effects
- No persistence
- No execution

---

### 9.2 Resolve (Design)

GetContextPackage(contextId) -> ContextPackage

---

### 9.3 Artifact Registration (Design)

RegisterArtifact(contextId, artifactRef)

- Design only
- No persistence in v1.6.0

---

## 10. Storage Model (Design Only)

Possible future options (non-binding):

- Git branch-based (`__factory_state__/contexts`)
- File-based (`factory/contexts/<contextId>.json`)
- External store

v1.6.0 constraint:

- Storage MAY be described
- Storage MUST NOT be implemented
- Any creation of `__factory_state__/contexts` (or similar) branches is forbidden in v1.6.0

---

## 10A. v1.7.0 Minimal Materialization (SSOT Storage Allowed)

This section is **normative for v1.7.0** and is the only allowed implementation scope.

### 10A.1 Allowed Storage (v1.7.0)

In v1.7.0, ContextPackage **MAY** be materialized as a single immutable JSON document written to a dedicated SSOT branch.

- SSOT branch: `__factory_state__/contexts`
- SSOT path: `factory/contexts/<contextId>.json`
- Write policy: **append-only by file creation** (create once; never modify)
- Immutability: once written, the file **MUST NOT** be changed or overwritten in v1.7.0.

### 10A.2 Generation Timing (v1.7.0)

- ContextPackage creation is allowed only for the **head job** of the Work Queue.
- ContextPackage creation **MUST** occur after the job is transitioned to `start` and before any job-specific work is executed.
- The implementation **MUST** fail-fast if the referenced `jobId` does not exist in the queue SSOT.

### 10A.3 Minimal Required Fields (v1.7.0)

A materialized ContextPackage document **MUST** include:
- `contextId` (format `ctx_<unix>_<rand4>`)
- `jobId`
- `createdAt` (RFC3339 UTC, seconds precision, MUST end with `Z`)
- `job` (a stable snapshot copied from the queue enqueue event):
  - `kind`, `repo`, `base`, `payload`
- `source` metadata:
  - `queueBranch`: MUST be `__factory_state__/work_queue`
  - `queuePath`: MUST be `factory/work_queue.jsonl`
  - `startEventId`: eventId of the `start` transition (if available)

The document **MUST NOT** include secrets, tokens, credentials, or any sensitive material.

### 10A.4 Idempotency / Uniqueness Rules (Hard)

- A `jobId` **MUST** map to exactly one `contextId`.
- If a ContextPackage already exists for a given `jobId`, creation **MUST** fail with an invariant violation.
- If a file already exists at `factory/contexts/<contextId>.json`, creation **MUST** fail (no overwrite).

### 10A.5 Locking (Hard)

All read-modify-write operations against the contexts SSOT branch **MUST** be guarded by a lock.

- Lock mechanism: reuse `RepoLock`
- Lock namespace: `__factory_lock__/contexts`
- Default TTL: 3600 seconds

### 10A.6 Exit Codes (Normative)

When implemented as CLI/worker processes, exit codes MUST be:
- `2`: blocked (head-of-queue blocked; no mutation performed)
- `3`: lock acquisition failure (contexts SSOT lock)
- `4`: invariant/schema violation (unknown jobId, non-head mutation, duplicate context)

---

## 11. Invariants (Hard)

- One jobId → one contextId
- ContextPackage is immutable
- No secrets allowed
- No runtime execution allowed
- Must remain compatible with head-only Work Queue semantics

---

## 12. Future Wiring (Non-Binding)

This section is informational only and MUST NOT justify implementation work.
These are non-binding and non-authoritative in this spec.
This section (and any examples/appendices) is informational and MUST NOT be used as justification for implementation work.

### 12.1 Non-Binding Examples (Hard)

Any example payloads, schemas, or diagrams in this document are illustrative.
They MUST NOT be used as implementation requirements in v1.6.0 and MUST NOT be used to justify adding runtime wiring.

---

## 13. Change Policy

- Changes MUST be made via Pull Request
- Human approval is mandatory
- Version-boundary changes that introduce runtime behavior require a CHANGELOG entry

---

## Appendix A: Example ContextPackage

```json
{
  "contextId": "ctx_1768109000_abcd",
  "jobId": "job_1768108900_1234",
  "repo": "milechy/Hetzner_AaaS_Factory",
  "base": "main",
  "actor": "milechy",
  "inputs": {
    "title": "Example task"
  },
  "lifecycle": {
    "state": "created",
    "createdAt": "2026-01-11T06:00:00Z"
  },
  "artifacts": [],
  "limits": {},
  "meta": {}
}
```

---

## 14. Exit Criteria (v1.6.0)

- ContextPackage SSOT is present on `main` (this spec).
- v1.6.0 introduces **design-only** constraints and does not create any contexts branch/file.
- No production code references ContextPackage in v1.6.0.
- No CI / workflow executes or persists ContextPackage in v1.6.0.

# END
