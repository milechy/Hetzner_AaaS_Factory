# ContextPackage Spec v1
# SSOT – Authoritative, Binding, Design-Only

Status: **DESIGN ONLY (v1.6.0)**  
Scope: Humans / GPT Projects / VS Code Agent / Copilot Agent

This document is **authoritative and binding**.
Anything not explicitly allowed here MUST NOT be implemented.

---

## 0. Purpose

The purpose of **ContextPackage** is to define a **stable, immutable execution context**
for a single Factory job.

In v1.6.0, ContextPackage is introduced as a **design artifact only**.

- It defines *what a job is allowed to see*
- It does NOT define *how a job is executed*
- It does NOT enable parallelism or isolation

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
  // ContextPackage is pure data (design-only in v1.6.0)
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

---

## 5. ID and Timestamp Rules (Normative)

- contextId format: `ctx_<unix>_<rand4>`
  - Example: `ctx_1768109000_abcd`
- `<unix>`: epoch seconds
- `<rand4>`: 4-character lowercase hex suffix
- IDs are generated once and MUST be treated as immutable identifiers (no re-generation).
- createdAt: RFC3339 UTC, seconds precision (MUST end with "Z")

---

## 6. Lifecycle Model (Design Only)

### 6.1 States (Conceptual)
- created
- running (future)
- done
- failed
- cancelled

### 6.2 Transition Rules
- In v1.6.0, lifecycle transitions are conceptual only
- No runtime transitions are allowed
- No state mutation is allowed

---

## 7. Relationship to Work Queue (Hard Boundary)
- Each jobId maps to exactly one contextId
- ContextPackage is conceptually created at job start
- ContextPackage MUST NOT be created during enqueue
- v1.6.0 MUST NOT write ContextPackage to disk or branch
- v1.6.0 MUST NOT introduce any production code path dependency on ContextPackage

WorkQueue jobId
      |
      | (conceptual start)
      v
ContextPackage contextId


---

## 8. Security and Data Handling
- ContextPackage MUST NOT store secrets
- Tokens and credentials MUST NOT be embedded
- Sensitive data MUST NOT be serialized
- ContextPackage is safe to log and inspect

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

Possible future options:
- Git branch-based (__factory_state__/contexts)
- File-based (factory/contexts/<contextId>.json)
- External store

v1.6.0 constraint:
- Storage options MAY be described as non-binding design notes
- Storage MUST NOT be implemented in v1.6.0

---

## 11. Invariants (Hard)
- One jobId → one contextId
- ContextPackage is immutable
- No secrets allowed
- No runtime execution allowed
- Must remain compatible with head-only Work Queue semantics

---

## 12. Future Wiring (Non-Binding)

The following MAY be introduced in v2.x:
- Worker materialization
- Context isolation
- Parallel execution
- Multi-AaaS contexts

These are non-binding and non-authoritative in this spec.
This section is informational and MUST NOT be used as justification for implementation work.

---

## 13. Change Policy
- Changes MUST be made via Pull Request
- Human approval is mandatory
- Version-boundary changes require CHANGELOG entry

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
- ContextPackage SSOT is merged to main.
- No production code path references ContextPackage (design-only boundary preserved).
- No CI/workflow changes introduce ContextPackage execution or persistence.
- No storage branches/files for ContextPackage are created in v1.6.0.

# END
