# Agent Execution Model Policy v1
# SSOT – Codex (Writer) + Opus 4.5 (Reviewer) Separation

## 0. Purpose

This policy defines **which model is allowed to do what** in the Factory execution loop, without breaking:
- PR-first / Human Gate
- Open-PR Contract + ToolGate
- RepoLock / PRScheduler / Work Queue invariants
- Evidence-based operation

This document is **normative**. If a model/role is not explicitly allowed here, it is **not allowed**.

---

## 1. Model Roles (Hard)

### 1.1 Codex = Writer (Execution / Implementation)
Codex is the **only** model allowed to produce write-intent artifacts:
- file edits (patches / writes) inside the allowed workspace scope
- test-fix loops (iterate until green or fail-fast threshold)
- PR proposal payload construction (title/body/diff summary)

Codex MUST NOT:
- bypass approval token / ToolGate
- push directly to remote (any `git push` outside `open_pr_cli` is forbidden)
- modify forbidden paths or core SSOT without explicit approval scope

### 1.2 Opus 4.5 = Reviewer (Read-only / Critique)
Opus 4.5 is a **read-only reviewer** used to reduce defect rate and SSOT drift.
Opus may:
- review diffs / proposed changes
- identify SSOT conflicts / missing invariants
- propose improvements as **comments** or “review notes”

Opus MUST NOT:
- call any tool that causes a write-side effect (filesystem, git, GitHub write)
- author the final patch contents
- decide to expand scope beyond the Task Brief

---

## 2. Tool Permissions by Role (Hard)

### 2.1 Common (Both roles may call)
Read-only tools only:
- repo_read_file / repo_list_files / repo_search
- gh_get_issue / gh_list_open_prs / gh_get_pr
- trace_event (no secrets)
- artifact_capture (read-only evidence snapshot)

### 2.2 Writer-only (Codex only)
Write-intent tools:
- workspace_apply_patch / workspace_write_file / workspace_diff_summary
- run_lint / run_tests / run_build (execution is allowed for Codex)
- summarize_failure (for iterative repair)
- open_pr_create (OpenPR CLI wrapper; requires approval_token)

### 2.3 Reviewer-prohibited (Opus)
Opus is prohibited from:
- any workspace_* write tool
- any run_* execution tool
- open_pr_create (or any GitHub write)
- any command runner that can mutate the environment

Rationale: Keep review deterministic and prevent “reviewer drift” into implementation.

---

## 3. Routing Requirements (Hard)

### 3.1 Routing is mandatory
Agents MUST NOT choose a model directly. They MUST call LLMRouter and specify only:
- `profile` (writer/reviewer)
- `risk_level` (low/medium/high)
- `task_kind` (implement/test/review/ssot_update)

### 3.2 Default routing
- Implementation / repair loop → `profile=writer` → Codex
- Review / critique / SSOT conflict check → `profile=reviewer` → Opus 4.5

### 3.3 High-risk separation
For `risk_level=high` tasks (infra/security/billing/contract/lock/queue):
- Writer remains Codex (execution discipline)
- Reviewer is mandatory (Opus 4.5 must review before PR creation)
- open_pr_create requires explicit approval scope including the high-risk area

---

## 4. Execution Loop Contract (Normative)

### 4.1 The only allowed write pipeline
1) Codex generates local changes (workspace-only)
2) Codex runs verification (lint/tests/build as applicable)
3) Opus reviews the diff and produces review notes
4) Codex applies review notes (workspace-only) if accepted
5) Human issues approval_token
6) Codex calls open_pr_create (ToolGate + PRScheduler + RepoLock enforced)
7) Human merges

### 4.2 Fail-fast constraints
- No waiting / retry loops on RepoLock or PRScheduler blocks.
- If blocked, emit the blocking reason and stop.

---

## 5. Evidence & Logging (Normative)

- Every tool call MUST emit a trace_event with:
  - role, profile, task_id, exit_code, files_touched_count
- No secrets may be written to logs or artifacts.
- For failed verification, artifact_capture MUST store a concise log excerpt.

---

## 6. Exceptions / Escalation

If review indicates scope expansion or SSOT drift:
- Opus must output “Escalate: SSOT update required” and stop.
- Codex must NOT implement the expansion until a new Task Brief is approved.

---

## 7. Versioning

- This policy is versioned (v1, v2, …).
- Any changes require PR + CHANGELOG update.

# END