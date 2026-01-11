# Changelog

All notable changes to this project are documented in this file.
This project follows a contract-first approach for controlled Git operations.

---

## [v1.6.0] - 2026-01-11

### Added
- ContextPackage specification (design-only; no runtime wiring)

---

## [v1.5.3] - 2026-01-11

### Added
- Work Queue SSOT transition (`transition-ssot`)
  - Head-of-queue のみが状態遷移可能（start / block / unblock / done / fail / cancel）
  - 非 head ジョブの mutation は即 FAIL（invariant violation）
  - `block` / `unblock` の human-only 制約を厳密に強制
  - すべての遷移は `__factory_state__/work_queue:factory/work_queue.jsonl` に追記

### Behavior Guarantees
- FIFO 不変条件を **実行時に強制**
- 同時 running は常に 1 件以下
- SSOT は append-only（rewrite / reorder 不可）
- 非人間 actor（`github-actions[bot]`）による状態遷移は不可

### CLI
- `work_queue_cli transition-ssot`
  - queue SSOT ブランチを fetch → switch → append → commit → push
  - exit codes:
    - `2`: head job が blocked
    - `3`: SSOT lock 取得失敗
    - `4`: schema / invariant violation

### Notes
- v1.5.3 は **Work Queue v1 の実運用遷移点**
- v1.5.0 = core 実装到達点
- v1.5.1 / v1.5.2 = IO 整備
- **v1.5.3 = Factory が queue を「動かせる」最小完成形**

---

## [v1.5.2] - 2026-01-11

### Added
- Work Queue SSOT IO: `enqueue-ssot`
  - `__factory_state__/work_queue:factory/work_queue.jsonl` に enqueue event を追記（git fetch/switch/commit/push）

---

## [v1.5.1] - 2026-01-11

### Changed
- Work Queue v1 spec の SSOT 整備（docs）

---

## [v1.5.0] - 2026-01-10

### Added
- Work Queue v1 core (SSOT-based)
  - JSONL queue parsing and event folding
  - FIFO invariants and head-of-queue enforcement
  - Human-only enqueue policy (reject `github-actions[bot]`)
  - Deterministic exit codes for queue operations

### Tests
- Add unit tests for queue invariants and illegal transitions

---

## [v1.4.3] - 2026-01-09

### Added
- RepoLock を OpenPR の write operations 境界として正式導入
  - open_pr_cli.py の write-side GitHub API 操作（branch 作成 / commit / PR 作成）を Repo-level fail-fast lock で保護
  - Lock ref: `refs/heads/__factory_lock__/open_pr`
  - Lock acquire は PRScheduler 通過後、最初の write 操作直前に実行
  - Lock release は finally ブロックで必ず実行（成功・失敗・例外時を含む）

### Changed
- PRScheduler と RepoLock の責務境界を明確化
  - PRScheduler: 論理的競合（既存 Factory PR の有無） の検出のみを担当
  - RepoLock: 物理的競合（同時 write operations） の防止を担当
  - 実行順序を固定:
    1. Approval / Contract validation
    2. PRScheduler check（read-only）
    3. RepoLock acquire
    4. Write operations
    5. RepoLock release

### Logging
- RepoLock のログを machine-parseable な key=value 形式に統一

### Tests
- RepoLock の acquire / release 挙動に対する unit tests を追加
- 422 / 404 / その他 API エラー時の fail-fast / warn / error 動作を明示的に検証

### Behavior Guarantees
- NO retry / NO wait policy は維持（fail-fast のみ）
- GitHub API エラー時の fail-safe / warn-only セマンティクスは変更なし
- 既存の OpenPR contract / exit code 規約に非互換変更なし

---

## [v1.4.2] - 2026-01-09

### Fixed
- Stabilize PRSchedule runtime logs to machine-parseable single-line key=value format.
- Standardize scheduler blocked handling in open_pr_cli to emit: `[PRSchedule] exit=2 blocked`.
- Strengthen unit tests to assert exact PRSchedule log output (no behavior changes).

---

## [v1.4.1] - 2026-01-09

### Changed
- Stabilize PRSchedule logging format to single-line key=value output.
  - Non-200 GitHub API responses now log:
    `[PRSchedule] warn reason=github_api_non_200 repo=<repo> base=<base> status=<code>`
  - Exceptions now log:
    `[PRSchedule] warn reason=github_api_exception repo=<repo> base=<base> exc=<ExceptionClass>`
  - Blocking condition now logs:
    `[PRSchedule] blocked reason=existing_open_factory_pr repo=<repo> base=<base> count=<N> first=<url>`

### Tests
- Strengthen PR scheduler tests to assert exact log output using `@patch('builtins.print')`.
- Preserve all existing behavioral guarantees (no logic changes).

---

## [v1.4.0] - 2026-01-08

### Added
- Minimal PR scheduling guardrail to prevent concurrent Factory PR creation on the same base branch.
  - Blocks when an existing open `proposal/*` PR targets the same base branch (exit code 2).
  - Fail-safe policy: on GitHub API errors, logs a warning and proceeds.

### Changed
- Run PR scheduler check before any write operations in `open_pr_cli.py`.

### Tests
- Add unit tests for PR scheduler blocking and fail-safe behavior.

---

## [v1.3.7] - 2026-01-06

### Changed
- Skip the GitHub Actions release workflow on bot-triggered tag pushes (prevents loops/duplicate runs).
- Stabilize the fully automated release flow by ensuring the release job runs only for human-created tags.

---

## [v1.3.0] - 2026-01-05

### Added
- **Open-PR Contract v1.3 SSOT**
  - Introduced `master__open_pr_contract_v1_3.md` as the single source of truth.
  - Explicit SSOT linkage metadata exposed by CLI (`contractVersion`, `ssotDocument`).
- **CLI contract discovery**
  - New `python -m controlled_git.cli contract --json` command for machine-readable contract inspection.
- **Approval token lifecycle controls**
  - Token expiration handling (`APPROVAL_EXPIRED`).
  - Token revocation via external revocation list (`APPROVAL_REVOKED`).
  - Mandatory-by-default `actorId` enforcement (`APPROVAL_ACTOR_MISMATCH`).
- **ToolGate context integrity enforcement**
  - Write-effect requires non-empty `pathsTouched`.
  - Absolute paths and `..` path segments are rejected.
  - `filesTouchedCount` must match unique `pathsTouched`.

### Changed
- **GitHub Open PR behavior**
  - GitHub API Base URL is now guarded; invalid or non-HTTPS values fall back to the default API base URL.
  - GitHub API 401/403 errors trigger a guaranteed browser-based PR creation fallback.

### Security
- Preserved fail-safe semantics: GitHub authorization failures never strand users.
- Approval token validation is enforced before any write-side effects.

---

## [v1.2.0]
- Initial Open-PR Contract with human approval gating.
- ToolGate-based permission checks for controlled Git operations.
