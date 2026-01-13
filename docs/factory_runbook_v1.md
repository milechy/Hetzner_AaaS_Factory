# Factory Runbook v1
# SSOT – Operational Guidance (v1.5.x stable, v1.6.0 design-aware)

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

### Design-Only (v1.6.0)

- ContextPackage
  - **NO runtime usage**
  - **NO storage**
  - **NO execution wiring**

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

## 9. v1.5.x 運用自動化（worker常駐化・監視）検討メモ（非拘束）

この節は **検討メモ（Design Notes）** であり、SSOT仕様・ロードマップの **拘束力を持たない**。
本節の記載は **v1.5.x の挙動変更を許可しない**（実装は別PR・別SSOT・別CHANGELOGで明示しない限り禁止）。

### 9.1 背景と目的

v1.5.x では Work Queue / RepoLock / Open-PR の安全ガードが揃ったが、運用上は次が課題になる:

- キュー処理の「手動トリガ」依存（継続運用では手間・抜けが出る）
- 異常（ブロック・ロック残留・API障害）の検知が遅れる
- ワーカの稼働状態が外形監視できない

目的（運用面）:

- **常駐ワーカ** または **定期ポーリング** により「キューが動かない」を減らす
- **監視/アラート** により「止まった/詰まった」を早期検知
- ただし **Fail-safe（停止優先）** と **Human Gate** を維持する

### 9.2 非目標（v1.5.x では禁止）

- 自動で PR をマージする
- Human Gate をバイパスする
- 並列実行（複数ワーカ/複数ジョブ同時）
- マルチレポ同時オーケストレーション
- ContextPackage の runtime 利用（v1.6.0 design-only）

### 9.3 運用自動化の実装候補（比較）

#### Option A: GitHub Actions（Scheduled / Repository Dispatch）

- 長所: 追加インフラ不要、監査ログがGitHubに残る
- 短所: 実行時間・頻度制約、ジョブが多いとレート/コスト/待ちが増える
- 適用: **低頻度で十分**（例: 5〜15分間隔のポーリング）な場合

#### Option B: Self-hosted Runner（常駐ワーカ）

- 長所: 常時稼働、即時反応、重い処理にも耐える
- 短所: ランナーの運用責任（再起動・更新・セキュリティ）
- 適用: 「キューを常に回したい」「即時性が必要」な場合

#### Option C: ローカル常駐（launchd/systemd）+ 手動操作の補助

- 長所: 最小構成で常駐/監視を作れる（Mac/Hetznerどちらでも）
- 短所: 環境依存、属人化しやすい
- 適用: 試験運用（PoC）向き

### 9.4 ワーカ常駐化で守るべきハード要件（運用）

- **単一ワーカ原則**: 同時に2つのワーカが動作してはならない（Work Queue の single-running と整合）
- **ロック順序**: 
  1) Queue lock（`__factory_lock__/work_queue`）で SSOT 読み書きを直列化
  2) RepoLock（`__factory_lock__/open_pr` 等）で対象リポジトリの書き込みを直列化
- **Head-of-queue のみ mutate**: `transition-ssot` は常に head を検証し、非headは FAIL（exit=4）
- **Fail-safe**: GitHub API が不安定 / 予期せぬ状態では「止まる」。再試行は限定的（バックオフ）
- **Human Gate 維持**: `block` → `unblock` は人間が判断（botによる自動解除は禁止）
- **監査可能性**: すべての操作は JSONL 追記 + key=value ログで追跡できる

### 9.5 監視（Observability）設計案

最小監視（推奨）:

- **Queue health**
  - head job の状態（queued/running/blocked）
  - 最終イベント時刻（staleness）
  - running が長時間継続（例: > 30分）
  - blocked が長時間継続（例: > 60分）

- **RepoLock health**
  - open_pr / work_queue namespace のロック残留
  - TTL を過ぎてもロックが解放されない（reap が効かない）

- **Worker health**
  - 実行ループの生存（heartbeat）
  - 異常終了回数（crash loop）

通知チャネル例（運用で選択）:

- GitHub Issue 作成（最小のエスカレーション）
- Slack/Webhook（外部通知）
- Email（代替）

注意: 通知実装は **秘密情報を含めない**。token/URL埋め込みは禁止。

### 9.6 期待する運用フロー（例）

- ワーカは一定間隔で SSOT（`__factory_state__/work_queue`）を読み、head のみを処理対象とする
- `blocked` を検知したら exit=2 で停止（自動解除はしない）
- `RepoLock` が取れない場合は exit=3 で停止（TTL待ち or 人間判断）
- 異常系では Issue / 通知を発行して人間に引き継ぐ

### 9.7 変更管理（重要）

- 本節の内容を実装に落とす場合は、必ず以下を満たす:
  - Roadmap（SSOT）で **Allowed** に入っていること
  - 仕様（SSOT）を先に確定すること
  - 変更は PR 経由で `main` に入り、必要なら CHANGELOG を伴うこと

---

## 10. Version Alignment

- v1.5.x: operationally complete
- v1.6.0: design-only expansion (ContextPackage)
- v2.x: NOT DEFINED

---

### References

- Detailed Work Queue operational procedures are defined in `docs/work_queue_operations_v1.md`.

---

# END
