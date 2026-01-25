# master__open_pr_contract_v1_3.md
================================================
AaaS Factory – Open PR Contract (v1.3)
Single Source of Truth (SSOT)
================================================

## 0. Purpose / Positioning
This document defines the authoritative contract for automated Pull Request creation
in the AaaS Factory.  
v1.3 is a backward-compatible extension of v1.2 and **does not weaken any safety
or fail-safe guarantees defined in v1.2**.

This SSOT takes precedence over:
- CLI behavior
- ToolGate policy implementation
- Agent-level heuristics
- README or examples

---

## 1. Compatibility Policy
- v1.3 MUST accept all valid v1.2-compliant executions.
- v1.3 MAY introduce stricter validation for malformed or ambiguous contexts.
- v1.2 behavior remains the baseline for:
  - fail-safe fallback on GitHub 401 / 403
  - actorId enforcement philosophy
  - allowlist-only write execution

---

## 2. Hard Requirements (MUST)
The following conditions MUST ALL be satisfied for any write-effect action
(including PR creation):

1. `humanApproved == true`
2. A valid Approval Token is provided
3. Approval Token signature is valid and not expired
4. `actorId` in token matches the executing actorId  
   - v1.3 maintains **mandatory-by-default** enforcement
5. ToolGate returns `allow`
6. No high-risk paths are involved (ToolGate and/or policy)

Failure of any item results in **write denial**.

---

## 3. Approval Token Contract (v1.3)

### 3.1 Required Fields (MUST)
An Approval Token MUST contain:

- `id` (UUID)
- `issuedAt` (ISO-8601)
- `expiresAt` (ISO-8601)
- `scope`:
  - `repo`
  - `baseBranch`
  - `proposalHash`
  - `actions`
  - `actorId`
- `signature` (HMAC-SHA256)

### 3.2 Actor Binding (MUST)
- The token is bound to a single `actorId`
- Any mismatch MUST be treated as a hard denial
- Denial reason SHOULD be machine-readable

**Actor ID Type:**
- `actorId` MUST be treated as an opaque string
- Numeric-only strings (e.g. "12345") are permitted
- Empty strings or whitespace-only values MUST be rejected
- RECOMMENDED: Use stable GitHub username (e.g. "milechy")

**Actor ID Source (Priority Order):**
1. `--actor` CLI argument (highest priority)
2. `CG_ACTOR` environment variable (Factory-specific)
3. `GITHUB_ACTOR` environment variable (GitHub Actions context)

If no actor ID is provided via any of the above sources, execution MUST be denied.

**Actor ID Validation:**
- Token scope MUST include `actorId` field
- Runtime `actorId` MUST match `token.scope.actorId` exactly (string comparison)
- Mismatch results in `APPROVAL_ACTOR_MISMATCH` (403-equivalent denial)
- Missing `actorId` in token scope results in denial

### 3.3 Revocation (OPTIONAL)
If `APPROVAL_REVOCATION_LIST_PATH` is configured:

- Token `id` MUST be checked against the revocation list
- A revoked token MUST be denied
- Revocation reason SHOULD be logged to audit output

Re-issuance is treated as issuance of a new token.

---

## 4. ToolGate Context Integrity (v1.3)

### 4.1 pathsTouched (MUST)
All entries in `pathsTouched` MUST satisfy:

- Relative paths only
- `/` as separator
- No leading `/`
- No `..` segments
- No empty strings

Evaluation MUST be done on:
```
unique(normalize(pathsTouched))
```

Violation results in denial.

### 4.2 filesTouchedCount (MUST)
- MUST equal `len(unique(normalize(pathsTouched)))`
- Any mismatch is treated as a **context integrity violation**
- Mismatch MUST be denied for effect="write" (v1.3)

### 4.3 Boundary Conditions (MUST)
- Write-effect actions with empty `pathsTouched` MUST be denied
- `maxFilesTouched` limits MUST be enforced
- `blockedWhen.pathsPrefix` MUST be evaluated against normalized paths

---

## 5. GitHub API Base URL (SHOULD + Guarded)

- Parameter: `GITHUB_API_BASE_URL`
- Default: `https://api.github.com`
- Trailing `/` MUST be stripped
- Empty or invalid values MUST fallback to default
- Fallback MUST emit a warning-level audit log

---

## 6. GitHub 401 / 403 Fail-Safe (MUST)

### 6.1 Fail-Safe Guarantee
GitHub API responses with status **401 or 403 MUST NOT abort execution**.

Instead:
- A fallback Pull Request creation URL MUST be returned:
  ```
  https://github.com/{owner}/{repo}/pull/new/{head}?expand=1
  ```

### 6.2 403 Reason Normalization (SHOULD)
403 responses SHOULD be classified on a best-effort basis.

Recommended `reason.code` values:
- `GITHUB_403_PAT_RESOURCE_NOT_ACCESSIBLE`
- `GITHUB_403_ORG_POLICY`
- `GITHUB_403_INSUFFICIENT_PERMISSIONS`
- `GITHUB_403_UNKNOWN`

Fail-safe behavior MUST NOT depend on classification success.

---

## 7. CLI Error Contract (v1.3)

### 7.1 Machine-Readable Errors (MUST)
CLI failures SHOULD expose structured error output.

Recommended format:
```
{
  "ok": false,
  "code": "<ERROR_CODE>",
  "message": "<human readable>",
  "details": { ... }
}
```

### 7.2 SSOT Linkage Metadata (MUST)
All `--json` outputs from `controlled_git` MUST include the following fields so that runtime artifacts can be traced back to this SSOT:

- `contractVersion`: fixed value `v1.3`
- `ssotDocument`: fixed value `master__open_pr_contract_v1_3.md`

The CLI MUST expose these values via:
```bash
python -m controlled_git.cli contract --json
```

### 7.3 Recommended Error Codes
- `APPROVAL_INVALID_SIGNATURE`
- `APPROVAL_EXPIRED`
- `APPROVAL_REVOKED`
- `APPROVAL_ACTOR_MISMATCH`
- `APPROVAL_SCOPE_MISMATCH`
- `TOOLGATE_DENY`
- `GITHUB_401`
- `GITHUB_403_*`
- `GITHUB_422_ALREADY_EXISTS`

### 7.4 Fallback Success
401 / 403 outcomes MUST be reported as:
- `ok: true`
- `status: "fallback"`
- `prCreateUrl` present

---

## 8. Audit Log Events (SHOULD)

Audit logging is best-effort and MUST NOT block execution.

Recommended events:
- `POLICY_CHECKED`
- `APPROVAL_ISSUED`
- `APPROVAL_VERIFIED`
- `APPROVAL_DENIED`
- `PR_OPEN_ATTEMPTED`
- `PR_OPENED`
- `PR_OPEN_FALLBACK`
- `PR_OPEN_FAILED`

Each event SHOULD include:
- timestamp
- actorId
- repo
- correlation/request id
- decision / status

---

## 9. Non-Goals
- This contract does NOT define UI behavior
- This contract does NOT mandate CI pipelines
- This contract does NOT override organization-level GitHub policy

---

## Factory Positioning (Decision)

- Factory is an AI development orchestration SDK.
- Claude Code / Codex / Opus / Grok / Qwen are execution engines, not the Factory itself.
- Factory development is human-driven with coding agents.
- Factory-orchestrated targets are developed automatically.
- Current milestone: Safe external-repo PR creation (proposal-only).

---

# END OF SSOT