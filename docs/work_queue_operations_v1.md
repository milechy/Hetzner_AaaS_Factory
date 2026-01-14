# Work Queue Operations v1
# SSOT – Authoritative, Binding (v1.5.x)

Status: **ACTIVE (v1.5.x)**  
Scope: Humans / Factory operators  

This document describes the **operational** procedures for the Work Queue introduced in v1.5.x.
It is not a design spec; it is the runbook.

---

## 0. Principles

- `main` is **protected**: changes land via PR only.
- Queue state is **operational SSOT** and lives on a dedicated branch:
  - `__factory_state__/work_queue`
  - path: `factory/work_queue.jsonl`
- Queue is **append-only** (JSONL). Current job state is derived by folding events in file order.
- Human-only policy:
  - Enqueue and `unblock` MUST NOT be performed by `github-actions[bot]`.
- Head-of-queue enforcement:
  - Only the **head non-terminal** job may be transitioned.

---

## 1. Components

### 1.1 Branches

- Product code: `main` (+ feature branches)
- Queue SSOT: `__factory_state__/work_queue`

### 1.2 Tools

- `tools/work_queue_cli.py`
  - `enqueue-ssot` (human enqueue; writes to SSOT branch)
  - `transition-ssot` (append head-only transitions; writes to SSOT branch)

### 1.3 Event Types

- `enqueue`, `start`, `block`, `unblock`, `done`, `fail`, `cancel`

---

## 2. Daily Operations

### 2.1 Check queue tail

```bash
git fetch origin __factory_state__/work_queue

git show origin/__factory_state__/work_queue:factory/work_queue.jsonl | tail -n 50
```

### 2.2 Enqueue (human-only)

```bash
python -m tools.work_queue_cli enqueue-ssot \
  --actor <your_login> \
  --kind open_pr \
  --repo <owner>/<repo> \
  --base main \
  --payload-json '{"title":"...","body":"..."}'
```

Expected:
- Prints `[WorkQueue] enqueue ok ... ssot_branch=__factory_state__/work_queue`
- Appends one JSON line to SSOT file.

### 2.3 Start head job

```bash
python -m tools.work_queue_cli transition-ssot \
  --actor <your_login> \
  --type start \
  --job-id <jobId>
```

Notes:
- Must be the **current head** job.
- If it is not head, the command must fail with an invariant violation.

### 2.4 Complete a job

```bash
python -m tools.work_queue_cli transition-ssot \
  --actor <your_login> \
  --type done \
  --job-id <jobId> \
  --reason "<short reason>"
```

### 2.5 Block / Unblock

Block (typically by operator when a human gate is required):

```bash
python -m tools.work_queue_cli transition-ssot \
  --actor <your_login> \
  --type block \
  --job-id <jobId> \
  --reason "awaiting_review"
```

Unblock (human-only):

```bash
python -m tools.work_queue_cli transition-ssot \
  --actor <your_login> \
  --type unblock \
  --job-id <jobId> \
  --reason "approved"
```

### 2.6 Fail / Cancel

Fail (running/blocked only):

```bash
python -m tools.work_queue_cli transition-ssot \
  --actor <your_login> \
  --type fail \
  --job-id <jobId> \
  --reason "<why>"
```

Cancel (queued/blocked only):

```bash
python -m tools.work_queue_cli transition-ssot \
  --actor <your_login> \
  --type cancel \
  --job-id <jobId> \
  --reason "<why>"
```

---

## 3. Invariants (Operator Checklist)

Before making any transition:

- The `jobId` exists.
- The `jobId` is the **head non-terminal**.
- State transition is legal:
  - `start`: queued → running
  - `block`: running → blocked
  - `unblock`: blocked → running
  - `done`/`fail`: running/blocked → terminal
  - `cancel`: queued/blocked → terminal
- At most one job is `running` at any time.

---

## 4. Exit Codes (CLI)

Normative exit codes:

- `2`: blocked (head-of-queue is blocked; no mutation performed)
- `3`: lock acquisition failure (queue lock could not be acquired / maintained)
- `4`: invariant violation or schema error

---

## 5. Scheduled Worker (Option A: GitHub Actions)

この節は Option A（GitHub Actions による定期実行/dispatch 実行）で Work Queue を進めるための運用手順である。
目的は「自動で進められるところは進める」だが、**Fail-safe と Human Gate を優先**し、
未知状態では停止する。

### 5.1 実行モデル

- Trigger: `schedule`（例: 5〜15分間隔）または `repository_dispatch`
- 実行は **単発のジョブ** とし、常駐プロセスは採用しない
- 多重起動防止:
  - GitHub Actions の `concurrency` を使い、同一ワークフローは同時に1つだけ実行

### 5.2 ワーカが行う最小処理（推奨順）

1) SSOT を読む（`__factory_state__/work_queue` / `factory/work_queue.jsonl`）
2) head job を導出する
3) head が `blocked` の場合は **exit=2**（人間判断待ち）
4) head が `queued` の場合は `start` を append（Work Queue CLI を利用）
5) job kind に応じた処理を実行
6) 成功なら `done`、失敗なら `fail` を append

### 5.3 ロック順序（必須）

- Queue lock → RepoLock の順に取得する。
  - Queue lock（`__factory_lock__/work_queue`）: Work Queue SSOT の read/append を直列化
  - RepoLock（例: `__factory_lock__/open_pr`）: 対象 repo の書き込みを直列化

### 5.4 Exit code と挙動

- `2`: blocked（head が blocked。ワーカは進めない）
- `3`: lock failure（Queue lock / RepoLock が取得できない）
- `4`: invariant/schema violation（不整合。ワーカは進めない）

### 5.5 例: GitHub Actions からの実行（概念）

Runbook/Operations は **秘密情報を文面に埋め込まない**。token は GitHub Secrets を使う。

- 例（概念）:
  - `python -m tools.work_queue_cli transition-ssot --actor github-actions[bot] --type start --job-id <jobId>`
  - `python tools/open_pr_cli.py ...`（Human Gate により block されることがある）

注意:
- `unblock` は人間のみ（bot が自動解除してはならない）
- 失敗時は “止まる” が正しい（再試行は最小・バックオフ）

---

## 6. Troubleshooting

### 6.1 "unknown_jobId"

Cause:
- You passed the wrong value (missing `job_` prefix, truncated, etc.).

Action:
- Re-copy jobId from SSOT JSONL line: `"jobId":"job_..."`.

### 6.2 "non_head_job_mutation"

Cause:
- Attempted to transition a non-head job.

Action:
- Transition the current head job first (usually complete or unblock it).

### 6.3 "human_only"

Cause:
- `actor` is `github-actions[bot]`.

Action:
- Re-run with your human login.

### 6.4 SSOT branch update conflicts

Symptom:
- Push rejected due to remote moving (someone appended events).

Action:
- Re-run the command; the CLI should refresh from origin.
- If manual recovery is needed:

```bash
# Safety: do not edit or rewrite history; only append.

git fetch origin __factory_state__/work_queue

git checkout __factory_state__/work_queue

git reset --hard origin/__factory_state__/work_queue
```

---

## 7. Emergency Procedures

### 7.1 Queue is corrupted (invalid JSONL line)

Policy:
- Do not rewrite SSOT history without explicit human decision.

Immediate containment:
- Stop automated consumers/workers.
- Capture evidence: save the tail and the exact offending line.

Preferred repair:
- Append a `fail` event for the head job (if possible) and re-enqueue.

### 7.2 Operator mistake (wrong transition)

Policy:
- Do not delete lines.

Repair:
- Append the next corrective event consistent with invariants.
  - Example: If a job was started and should be canceled, append `fail` with reason `operator_cancel`.

---

## 8. Release/Tagging Notes (v1.5.x)

- Tags/releases are separate from “code landing”.
- Changelog updates must go via `release/*-changelog` PR flow.
- If `main` is protected by repository rules, direct pushes are expected to fail.

---

## 9. Appendix: Quick Commands

```bash
# Show queue tail

git fetch origin __factory_state__/work_queue

git show origin/__factory_state__/work_queue:factory/work_queue.jsonl | tail -n 30

# Enqueue

python -m tools.work_queue_cli enqueue-ssot --actor <you> --kind open_pr --repo <o>/<r> --base main --payload-json '{"title":"..."}'

# Start head

python -m tools.work_queue_cli transition-ssot --actor <you> --type start --job-id <jobId>

# Done

python -m tools.work_queue_cli transition-ssot --actor <you> --type done --job-id <jobId> --reason "ok"
```

# END