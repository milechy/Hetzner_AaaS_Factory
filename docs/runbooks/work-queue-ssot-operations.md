# SSOT Operations Runbook (Work Queue / Contexts)

This runbook is the authoritative procedure for mutating SSOT JSONL files.

- Work Queue SSOT: `factory/work_queue.jsonl` on branch `__factory_state__/work_queue`
- Contexts SSOT: `factory/contexts.jsonl` on branch `__factory_state__/contexts`

## Non-negotiables

- SSOT files are **append-only** (one JSON object per line)
- History must be **linear** (no merge/rebase/cherry-pick)
- SSOT mutations must be done from **dedicated git worktrees**
- Always `git pull --ff-only` in the SSOT worktree right before appending

If you deviate from this runbook, conflicts and silent corruption become likely.

---

## Quick Start (One-time setup)

From the main repo directory:

```bash
cd Hetzner_AaaS_Factory

# Work Queue SSOT worktree
# NOTE: create a local worktree branch name (ssot/work_queue) to avoid collisions.
git fetch origin __factory_state__/work_queue
git worktree add -b ssot/work_queue ../Hetzner_AaaS_Factory__queue origin/__factory_state__/work_queue

# Contexts SSOT worktree
# NOTE: create a local worktree branch name (ssot/contexts) to avoid collisions.
git fetch origin __factory_state__/contexts
git worktree add -b ssot/contexts ../Hetzner_AaaS_Factory__contexts origin/__factory_state__/contexts
```

Expected layout:

```
Hetzner_AaaS_Factory/              # main development repo (stay on main)
Hetzner_AaaS_Factory__queue/       # SSOT worktree: __factory_state__/work_queue
Hetzner_AaaS_Factory__contexts/    # SSOT worktree: __factory_state__/contexts
```

Important: `git worktree add … origin/<branch>` often checks out a **detached HEAD**. That is OK.
Do **not** immediately try to create/switch a local branch named `__factory_state__/…` inside the worktree.
You can commit and push from detached HEAD safely.

### If you previously checked out __factory_state__/... in the main repo

If you ever ran `git switch __factory_state__/work_queue` (or `.../contexts`) in the *main* repo, Git will “attach” that branch to the main worktree. This causes errors like:

- `fatal: '__factory_state__/work_queue' is already used by worktree at ...`
- `fatal: a branch named '__factory_state__/work_queue' already exists`

Fix (safe, from the main repo):

```bash
cd Hetzner_AaaS_Factory

# 1) ensure main repo is on main
git switch main

# 2) confirm which worktree owns what
git worktree list

# 3) if the local branch exists and is not needed, delete it
# (we intentionally use ssot/* local branches for worktrees instead)
git branch -D __factory_state__/work_queue 2>/dev/null || true
git branch -D __factory_state__/contexts 2>/dev/null || true

# 4) prune stale worktree metadata
git worktree prune
```

Then re-run the Quick Start worktree setup (it will recreate the safe `ssot/*` local worktree branches).

---

## Why this runbook exists

`factory/work_queue.jsonl` is a **Single Source of Truth (SSOT)**.  
It is mutated by both humans and GitHub Actions.

Without strict rules, this file WILL drift, conflict, or corrupt history.

This document defines the **only supported way** to touch the Work Queue SSOT.

---

## 1. Preconditions / Mental Model

Before doing anything, understand this:

- `factory/work_queue.jsonl` is **append-only**  
- History MUST be linear  
- There is **no merge**, **no rebase**, **no cherry-pick**  
- SSOT is NOT operated from `main`

If you violate this, conflicts and silent corruption WILL occur.

---

## 2. Golden Rules (絶対ルール)

1. Never edit Work Queue SSOT from the primary repo working tree (`Hetzner_AaaS_Factory/`)  
2. Always use the dedicated worktree (`Hetzner_AaaS_Factory__queue/`) for SSOT mutation  
3. Detached HEAD in the worktree is normal — you may commit and push without creating a local branch  
4. Only append new JSONL lines (single-line JSON; no pretty-print)  
5. Always `git pull --ff-only` in the SSOT worktree immediately before appending  
6. Push ONLY to `__factory_state__/work_queue`  
7. If a conflict happens, you already broke the rules — abort  

---

## 3. Repository Layout (Expected)

```
Hetzner_AaaS_Factory/              # main development repo
Hetzner_AaaS_Factory__queue/       # SSOT-only worktree
```

- The main repo is for code, docs, PRs  
- The `__queue` worktree is ONLY for SSOT operations  

---

## 4. Initial One-Time Setup (Required)

Run this **once**:

```bash
cd Hetzner_AaaS_Factory
git fetch origin __factory_state__/work_queue
git worktree add ../Hetzner_AaaS_Factory__queue origin/__factory_state__/work_queue
```

Result:  
- isolated SSOT workspace  
- no accidental branch switching  
- safe coexistence with GitHub Actions  

---

## 5. Reading the Queue (Safe)

```bash
cd ../Hetzner_AaaS_Factory__queue
git pull --ff-only
less factory/work_queue.jsonl
```

Reading is always safe.

---

## 5.1 Common Pitfalls and Why They Happen

### A) “SSOT file changed automatically”

This is expected.  
GitHub Actions (worker/executor) append new events to the SSOT branch. If you fetched or switched branches and the file content moved, it is usually because the **remote SSOT branch advanced** (not because your local git “auto-edited” the file).

Correct response (in the SSOT worktree):

```bash
git pull --ff-only
```

Do not try to “restore” the file to what you saw earlier.

---

### B) “Your local changes would be overwritten by checkout” when switching to SSOT branch

This happens when you touched `factory/work_queue.jsonl` in a non-SSOT branch/worktree and then tried to switch.

Correct response:

- If you do **not** intend to keep those local changes: discard them.  
  ```bash
  git restore --source=HEAD -- factory/work_queue.jsonl
  ```
- If you do intend to keep them: stop and redo the operation from the SSOT worktree using the enqueue procedure.

**Best practice:** do not try to solve this by switching branches in-place. Create (or use) the SSOT worktree and perform the enqueue/append there.

---

### C) “a branch named '__factory_state__/work_queue' already exists”

This is normal if you already created the local branch once.  
You do not need to create it again.

In worktree-based operation, you can simply work on detached HEAD and push to the remote SSOT branch.

---

### D) “'__factory_state__/work_queue' is already used by worktree at …”

This means some other worktree is currently attached to that local branch name.  
Most commonly: you previously checked out `__factory_state__/work_queue` inside the main repo.

Fix:

1) In the main repo, switch back to `main`:  
   ```bash
   cd Hetzner_AaaS_Factory
   git switch main
   ```

2) List worktrees and confirm who owns the branch:  
   ```bash
   git worktree list
   ```

3) If the main repo is still registered as using the SSOT branch, prune stale entries:  
   ```bash
   git worktree prune
   ```

After that, do SSOT operations only from the dedicated SSOT worktree.

---

## 6. Enqueue a Job (Manual Operation)

### 6.1 Pull latest SSOT

First, confirm you are in the SSOT worktree:

```bash
pwd
# expected: .../Hetzner_AaaS_Factory__queue

git rev-parse --abbrev-ref HEAD
# expected: HEAD (detached) or __factory_state__/work_queue
```

Then fast-forward pull:

```bash
git pull --ff-only
```

If this fails → STOP (someone else advanced SSOT; you must synchronize before appending).

---

### 6.2 Append exactly one event

Edit the file:

```bash
vim factory/work_queue.jsonl
```

Append ONE line only:

```json
{
  "eventId": "evt_<unique>",
  "ts": "<ISO8601 UTC>",
  "actor": "<your name>",
  "type": "enqueue",
  "jobId": "<job id>",
  "job": { ... }
}
```

Never modify existing lines.

---

### 6.3 Commit

```bash
git add factory/work_queue.jsonl
git commit -m "chore(queue): enqueue <short description>"
```

---

### 6.4 Push (explicit SSOT push)

```bash
git push origin HEAD:__factory_state__/work_queue
```

Done.

---

## 7. What is Normal (Not Errors)

### File changed automatically

Cause:  
- worker or executor appended events

Action:

```bash
git pull --ff-only
```

Continue.

---

## 8. What Is NOT Allowed

❌ Editing SSOT from `main`  
❌ `git switch __factory_state__/work_queue` in main repo  
❌ cherry-pick into SSOT  
❌ rebase / merge  
❌ force-push  

---

## 9. If You See a Conflict

This means:  
- rules were violated

Recovery (run inside `Hetzner_AaaS_Factory__queue/`):

```bash
# if you started a merge/cherry-pick by mistake
git merge --abort 2>/dev/null || true
git cherry-pick --abort 2>/dev/null || true

# hard reset to the remote SSOT tip
git fetch origin __factory_state__/work_queue
git reset --hard origin/__factory_state__/work_queue
```

Then start again at step 6.

---

## 10. Automation (Worker / Executor)

GitHub Actions follow the same rules:

- fetch SSOT  
- append ONE event  
- commit with bot identity  
- push HEAD → SSOT branch  

They MUST behave exactly like a human operator using this runbook.

---

## Final Note

If you feel friction, the rules are working.

SSOT safety is more important than convenience.

---

# Context SSOT Operations Runbook

## Goal: “same type” contract (Context SSOT v1)

Context SSOT uses the same *event envelope* pattern as Work Queue SSOT:

- JSONL (1 JSON object per line)
- append-only
- linear history
- common fields: `eventId`, `ts`, `actor`, `type`

### Context SSOT v1 envelope

All non-init events MUST include:

- `eventId`: unique string (recommend `evt_<unix>_<rand>`)
- `ts`: ISO8601 UTC (`...Z`)
- `actor`: human name or `github-actions[bot]`
- `type`: one of the supported context event types
- `contextId`: stable identifier for the context

### Minimal example (materialize)

```json
{"eventId":"evt_1700000000_abcd","ts":"2026-01-14T11:00:00Z","actor":"github-actions[bot]","type":"materialize","contextId":"ctx_abc123","spec":{"source":"milechy/Hetzner_AaaS_Factory@66d51cb","inputs":{},"version":"v1"}}
```

This keeps the SSOT “shape” consistent across files and makes shared tooling (validators, tailers, fold/state recon) straightforward.

## Why this runbook exists

`factory/contexts.jsonl` is a **Single Source of Truth (SSOT)** for Context lifecycle.  
It is mutated by both humans and GitHub Actions.

Without strict rules, this file WILL drift, conflict, or corrupt history.

This document defines the **only supported way** to touch the Context SSOT.

---

## 1. Preconditions / Mental Model

Before doing anything, understand this:

- `factory/contexts.jsonl` is **append-only** (JSONL 追記のみ)  
- History MUST be linear (no merge / rebase)  
- There is **no merge**, **no rebase**, **no cherry-pick**  
- Context SSOT is NOT operated from `main`

If you violate this, conflicts and silent corruption WILL occur.

---

## 2. Golden Rules (絶対ルール)

1. Never edit Context SSOT from the primary repo working tree (`Hetzner_AaaS_Factory/`)  
2. Always use the dedicated worktree (`Hetzner_AaaS_Factory__contexts/`) for SSOT mutation  
3. Detached HEAD in the worktree is normal — you may commit and push without creating a local branch  
4. Only append new JSONL lines (single-line JSON; no pretty-print)  
5. Always `git pull --ff-only` in the SSOT worktree immediately before appending  
6. Push ONLY to `__factory_state__/contexts`  
7. If a conflict happens, you already broke the rules — abort  

---

## 3. Repository Layout (Expected)

```
Hetzner_AaaS_Factory/              # main development repo
Hetzner_AaaS_Factory__queue/       # Work Queue SSOT-only worktree
Hetzner_AaaS_Factory__contexts/    # Context SSOT-only worktree
```

- The main repo is for code, docs, PRs
- The `__contexts` worktree is ONLY for Context SSOT operations

---

## 4. Initial One-Time Setup (Required)

Run this **once**:

```bash
cd Hetzner_AaaS_Factory
git fetch origin __factory_state__/contexts
git worktree add ../Hetzner_AaaS_Factory__contexts origin/__factory_state__/contexts
```

Result:
- isolated Context SSOT workspace
- no accidental branch switching
- safe coexistence with GitHub Actions

---

## 5. Reading the Context SSOT (Safe)

```bash
cd ../Hetzner_AaaS_Factory__contexts
git pull --ff-only
less factory/contexts.jsonl
```

Reading is always safe.

---

## 6. Event Model (SSOT Schema)

### 6.1 File header (required)

The first line MUST be:

```json
{"type":"__init__","note":"SSOT file placeholder; events start below"}
```

### 6.2 Common fields

All non-init events MUST include:

- `eventId` (unique)
- `ts` (ISO8601 UTC, `...Z`)
- `actor` (human or `github-actions[bot]`)
- `type` (event type)
- `contextId`

### 6.3 Supported event types

#### (1) materialize

Context を生成（または再生成）した事実。

```json
{
  "eventId": "evt_<unique>",
  "ts": "<ISO8601 UTC>",
  "actor": "<actor>",
  "type": "materialize",
  "contextId": "ctx_<id>",
  "spec": {
    "source": "<repo>@<ref>",
    "inputs": {},
    "version": "v1"
  }
}
```

#### (2) update

Context に意味的変更が入った事実（例: schema bump）。

```json
{
  "eventId": "evt_<unique>",
  "ts": "<ISO8601 UTC>",
  "actor": "<actor>",
  "type": "update",
  "contextId": "ctx_<id>",
  "delta": {
    "reason": "<reason>",
    "from": "v1",
    "to": "v2"
  }
}
```

#### (3) invalidate

Context を無効化（再利用不可）した事実。

```json
{
  "eventId": "evt_<unique>",
  "ts": "<ISO8601 UTC>",
  "actor": "<actor>",
  "type": "invalidate",
  "contextId": "ctx_<id>",
  "reason": "<reason>"
}
```

#### (4) gc (optional / future)

TTL 到達などで物理削除した事実（将来用）。

```json
{
  "eventId": "evt_<unique>",
  "ts": "<ISO8601 UTC>",
  "actor": "<actor>",
  "type": "gc",
  "contextId": "ctx_<id>",
  "policy": "ttl-expired"
}
```

---

## 7. Folding Rules (State Reconstruction)

Context の状態は `contextId` 単位で最後のイベントで決まる。

| last event | state |
|---|---|
| materialize | active |
| update | active |
| invalidate | invalid |
| gc | removed |

Note: Work Queue と違い、Context SSOT は「head job」や順序制約は持たない（`contextId` ごとに独立）。

---

## 8. Manual Operations

### 8.1 Pull latest SSOT

First, confirm you are in the SSOT worktree:

```bash
pwd
# expected: .../Hetzner_AaaS_Factory__contexts

git rev-parse --abbrev-ref HEAD
# expected: HEAD (detached) or __factory_state__/contexts
```

Then fast-forward pull:

```bash
git pull --ff-only
```

If this fails → STOP (someone else advanced SSOT; you must synchronize before appending).

### 8.2 Append exactly one event

Edit the file:

```bash
vim factory/contexts.jsonl
```

Append ONE line only (single-line JSON; no pretty-print):

- materialize / update / invalidate / gc のいずれか
- 既存行は絶対に変更しない

### 8.3 Commit

```bash
git add factory/contexts.jsonl
git commit -m "chore(contexts): <event type> <short description>"
```

### 8.4 Push (explicit SSOT push)

```bash
git push origin HEAD:__factory_state__/contexts
```

Done.

---

## 9. What is Normal (Not Errors)

### File changed automatically

Cause:
- worker / executor が `factory/contexts.jsonl` にイベントを追記した

Action:

```bash
git pull --ff-only
```

Continue.

---

## 10. What Is NOT Allowed

❌ Editing Context SSOT from `main`  
❌ `git switch __factory_state__/contexts` in main repo  
❌ cherry-pick into Context SSOT  
❌ rebase / merge  
❌ force-push

---

## 11. If You See a Conflict

This means:
- rules were violated

Recovery (run inside `Hetzner_AaaS_Factory__contexts/`):

```bash
git merge --abort 2>/dev/null || true
git cherry-pick --abort 2>/dev/null || true

git fetch origin __factory_state__/contexts
git reset --hard origin/__factory_state__/contexts
```

Then start again at step 8.

---

## 12. Automation (Worker / Executor)

GitHub Actions MUST follow the same rules:

- fetch SSOT  
- append ONE event  
- commit with bot identity  
- push HEAD → SSOT branch  

They MUST behave exactly like a human operator using this runbook.

---

## Final Note

If you feel friction, the rules are working.

Context SSOT safety is more important than convenience.

---

## Next: Automation alignment

To keep SSOT stable, GitHub Actions must behave exactly like a human following this runbook:

1) fetch SSOT branch  
2) checkout SSOT ref (detached HEAD is OK)  
3) append exactly one JSONL event  
4) commit with bot identity  
5) push `HEAD:__factory_state__/…`

Additionally, when calling external APIs (e.g., GitHub PR create), do not treat HTTP 422 as “already exists” by default.  
Parse the error payload and classify the reason (missing head, invalid ref, permission, already exists, etc.).

### Next development PR checklist

1) Add a small Python validator used by both workflows:
   - validate JSONL line-by-line
   - enforce `__init__` header
   - enforce required fields per SSOT (queue vs contexts)
2) Make workflows fail-fast if SSOT validation fails (before mutating)
3) For `open_pr`, treat HTTP 422 as **non-terminal until classified**:
   - branch missing (invalid `head`)
   - PR already exists
   - base/head invalid combination
4) Ensure the executor always mutates the SSOT branch it read (no “read from origin/X, write to working tree”).