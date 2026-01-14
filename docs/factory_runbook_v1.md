# Factory Runbook v1
# SSOT – Operational Guidance (v1.5.x stable, v1.7.0 minimal ContextPackage SSOT)

Status: **ACTIVE (Operations)**  
Applies to: Humans operating the Factory repository  
Scope: Release Factory, Work Queue, RepoLock, Open-PR automation

This document defines **how to operate, diagnose, and recover** the Factory
as of **v1.5.x**.  
It is complementary to SSOT specs and MUST NOT introduce new behavior.

---

## 0. Principles (Hard)

- **main is protected**: all changes via PR only
- **SSOT-first**: operational state lives in explicit SSOT branches/files
- **Fail-safe over progress**: blocking is preferred to corruption
- **Human gate is mandatory** at all decision points

---

## 1. Current Factory Capabilities (Evidence-Based)

### Implemented & Stable (v1.5.x)

- Release Factory (CHANGELOG-driven)
- Open-PR automation with Human Gate
- RepoLock (repo-level safety guard, TTL-based)
- Work Queue v1:
  - JSONL SSOT
  - FIFO
  - Single-running invariant
  - Human-only enqueue
  - Head-only transitions

### Implemented (v1.7.0, Minimal)

- ContextPackage SSOT materialization (storage-only)
  - Creates immutable ContextPackage documents on `__factory_state__/contexts`
  - NO runtime usage / NO execution wiring / NO orchestration triggers
  - Duplicate materialization for the same `jobId` is rejected
  - Exit codes (aligned with Work Queue CLI):
    - 2: head job is blocked
    - 3: RepoLock acquisition failed
    - 4: schema / invariant violation

### Design-Only (v1.6.0)

- ContextPackage (beyond v1.7.0 minimal materialization)
  - **NO runtime usage**
  - **NO execution wiring**
  - **NO orchestration / automation triggers**

---

## 2. Operational Branches (SSOT)

### main
- Product code
- Specs
- Docs
- CHANGELOG

### __factory_state__/work_queue
- **Operational SSOT**
- File: `factory/work_queue.jsonl`
- Written by:
  - Human CLI
  - Factory worker tools
- No PR required (operational state only)

### __factory_state__/contexts
- ContextPackage SSOT (v1.7.0 minimal)
- Directory: `factory/contexts/`
- Written by:
  - Human CLI (`python tools/context_package_cli.py materialize-ssot`)
- Create-only (immutable): existing documents MUST NOT be modified or deleted
- No PR required (operational state only)

### __factory_lock__/*
- RepoLock namespaces
- Ephemeral safety artifacts
- TTL-governed

---

## 3. Work Queue Operations (v1.5.x)

### 3.1 Enqueue (Human Only)

Command:
```
python -m tools.work_queue_cli enqueue-ssot \
  --actor <human> \
  --kind <open_pr|release|changelog|maintenance> \
  --repo owner/name \
  --base main \
  --payload-json '{...}'
```

Rules:
- Actor MUST NOT be `github-actions[bot]`
- Appends `enqueue` event only
- Does NOT start execution

### 3.2 Transitions (Head Only)

Allowed types:
- start
- block
- unblock
- done
- fail
- cancel

Command:
```
python -m tools.work_queue_cli transition-ssot \
  --actor <human|worker> \
  --type <transition> \
  --job-id <jobId>
```

Hard invariants:
- Only head-of-queue job may transition
- Only one running job globally
- unblock MUST be human-triggered

Exit codes:
- 2: blocked
- 3: lock failure
- 4: invariant/schema violation

---

## 4. RepoLock Operations

### Purpose
Prevent concurrent mutation of the same repo.

### Characteristics
- Implemented via Git refs
- Namespaced per feature (e.g. open_pr, work_queue)
- TTL-based reaping (default: 3600s)

### Emergency Unlock (Manual)

List locks:
```
gh api repos/:owner/:repo/git/matching-refs/heads/__factory_lock__
```

Delete lock:
```
gh api -X DELETE repos/:owner/:repo/git/refs/heads/__factory_lock__/<path>
```

Use ONLY if automation is fully stopped.

### Common Failure: 403 (PAT insufficient for Git refs)

Symptom:
- RepoLock acquire fails with `status=403` and/or GitHub reports:
  - `Resource not accessible by personal access token`
  - `TOKEN_INSUFFICIENT_FOR_GIT_REFS`

Cause:
- The token can authenticate (e.g. `GET /user` works) but lacks permission to create Git refs via `POST /repos/:owner/:repo/git/refs`.

Action:
- Regenerate the token (PAT) and ensure it has repository write permissions sufficient to create refs.
- Re-run the failed CLI command after updating `GITHUB_TOKEN`.

Notes:
- This is a token permission issue, not a lock collision.
- A real lock collision typically appears as `status=422` (already_locked).

---

## 5. Release Operations

### Release Source of Truth
- `CHANGELOG.md`

### Release Flow
1. CHANGELOG PR merged
2. Tag created automatically
3. GitHub Release generated

Rules:
- No direct tagging
- No manual release edits
- vX.Y.Z tag MUST point to CHANGELOG commit

---

## 6. Incident Response

### Symptoms → Actions

**Queue stuck (blocked)**
- Inspect head job
- Check `block` reason
- Human decides unblock or cancel

**RepoLock collision**
- Verify no parallel automation
- Wait for TTL
- Manual delete ONLY if safe

**CI failing on changelog-pr**
- Confirm CHANGELOG format
- Ensure PR title/version alignment

---

## 7. Explicit Prohibitions

- Editing SSOT state on `main`
- Parallel job execution
- Multi-repo orchestration
- Using ContextPackage at runtime (v1.6.0)
- Auto-merging PRs
- Bypassing Human Gate

Any of the above is a **policy violation**.

---

## 8. Escalation Checklist

Before manual intervention:
- Is automation paused?
- Is SSOT consistent?
- Is the action reversible?
- Is a log entry preserved?

If NO → STOP.

---

## 9. 運用自動化（Option A: GitHub Actions Scheduled Worker）

この節は **運用ガイダンス（Operations）** であり、設計メモではない。
ここで述べる運用は **v1.7.x の SSOT 運用（Work Queue / RepoLock）** の範囲に限定し、
**Human Gate（block/unblock の人間判断）** と **Fail-safe** を維持する。

### 9.1 目的

- キュー処理の「手動トリガ」依存を減らし、運用の抜け漏れを減らす
- blocked / lock / API 障害などを早期に検知し、停止（fail-safe）できるようにする

### 9.2 採用方針（Option A）

- GitHub Actions の **schedule** もしくは **repository_dispatch** を入口にし、
  **単一のワーカ実行**（同時多重起動しない）で Work Queue を進める
- 実際の手順・コマンド・チェックリストは **Work Queue Operations** に集約する（Runbook は方針のみ）

参照:
- `docs/work_queue_operations_v1.md`（“Scheduled Worker (Option A)” 節）

### 9.3 ハード要件（再掲）

- **単一ワーカ原則**（同時に2つのワーカが動作してはならない）
- **ロック順序**:
  1) Queue lock（`__factory_lock__/work_queue`）で SSOT 読み書きを直列化
  2) RepoLock（`__factory_lock__/open_pr` 等）で対象リポジトリの書き込みを直列化
- **Head-of-queue のみ mutate**（非headは FAIL: exit=4）
- **Human Gate 維持**（block → unblock は人間のみ）
- **Fail-safe**（未知/不整合/外部障害では進めず停止）

---

## 10. Version Alignment

- v1.5.x: operationally complete
- v1.6.0: design-only expansion (ContextPackage)
- v2.x: NOT DEFINED

---

### References

- Detailed Work Queue operational procedures are defined in `docs/work_queue_operations_v1.md`.

---
