# Changelog

All notable changes to this project are documented in this file.
This project follows a contract-first approach for 
controlled Git operations.

⸻

## Unreleased
- Add v1.7.0 roadmap entry for ContextPackage SSOT materialization (minimal).

⸻

## [v1.5.3] - 2026-01-11

### Added
- Work Queue SSOT transition (`transition-ssot`)
  - Head-of-queue のみが状態遷移可能（start / block / unblock / done / fail / cancel）
  - 非 head ジョブの mutation は即 FAIL（invariant violation）
  - `blocked` / `unblock` の human-only 制約を厳密に強制
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
  v1.5.1 / v1.5.2 = IO 整備  
  **v1.5.3 = Factory が queue を「動かせる」最小完成形**

⸻

## [v1.5.2] - 2026-01-11

### Added
- Work Queue SSOT IO: `enqueue-ssot` writes queue events to `__factory_state__/work_queue:factory/work_queue.jsonl` via git fetch/switch/commit/push.

⸻

## [v1.5.0] - 2026-01-10

### Added
- Work Queue v1 core (SSOT-based): JSONL queue parsing and event folding
- FIFO invariants and head-of-queue enforcement
- Human-only enqueue policy (reject github-actions[bot])
- Deterministic exit codes for queue operations

### Tests
- Add unit tests for queue invariants and illegal transitions

⸻

[v1.4.3] - 2026-01-09

Added
	•	RepoLock を OpenPR の write operations 境界として正式導入
	•	open_pr_cli.py のすべての write-side GitHub API 操作（branch 作成 / commit / PR 作成）を
Repo-level fail-fast lock で明示的に保護。
	•	Lock ref: refs/heads/__factory_lock__/open_pr
	•	Lock acquire は PRScheduler 通過後、最初の write 操作直前に実行。
	•	Lock release は finally ブロックで必ず実行（成功・失敗・例外時を含む）。

Changed
	•	PRScheduler と RepoLock の責務境界を明確化
	•	PRScheduler: 論理的競合（既存 Factory PR の有無） の検出のみを担当。
	•	RepoLock: 物理的競合（同時 write operations） の防止を担当。
	•	両者の順序を以下に固定：
	1.	Approval / Contract validation
	2.	PRScheduler check（read-only）
	3.	RepoLock acquire
	4.	Write operations
	5.	RepoLock release

Logging
	•	RepoLock のログを machine-parseable な key=value 形式に統一：
	•	Acquire success:
[RepoLock] acquire ok repo=<repo> ref=<ref>
	•	Acquire conflict (422):
[RepoLock] acquire fail reason=already_locked repo=<repo> ref=<ref> status=422
	•	Release success:
[RepoLock] release ok repo=<repo> ref=<ref>
	•	Release not found (404):
[RepoLock] release warn reason=not_found (may have been manually deleted)
	•	Release API error:
[RepoLock] release fail reason=github_api_error repo=<repo> ref=<ref> status=<code>

Tests
	•	RepoLock の acquire / release 挙動に対する unit tests を追加。
	•	422 / 404 / その他 API エラー時の fail-fast / warn / error 動作を明示的に検証。
	•	PRScheduler / RepoLock の両方が独立してテスト可能な構造を維持。

Behavior Guarantees
	•	NO retry / NO wait policy は維持（fail-fast のみ）。
	•	GitHub API エラー時の fail-safe / warn-only セマンティクスは変更なし。
	•	既存の OpenPR contract / exit code 規約に非互換変更なし。

⸻

補足（運用メモ・非記載）
	•	このリリースは 設計整理＋安全性強化のみで、外部挙動は意図的に不変。
	•	v1.4.x 系の「競合防止モデル」はこの時点で完成形。

---

## [v1.5.3] - 2026-01-11

### Changed
- feat(queue): Work Queue SSOT transition (v1.5.3) (#45)
  - https://github.com/milechy/Hetzner_AaaS_Factory/pull/45

---

## [v1.5.2] - 2026-01-11

### Changed
- feat(queue): Work Queue SSOT IO (enqueue-ssot) v1.5.2 (#43)
  - https://github.com/milechy/Hetzner_AaaS_Factory/pull/43

---

## [v1.5.1] - 2026-01-11

### Changed
- Docs/v1.5.0 work queue spec (#37)
  - https://github.com/milechy/Hetzner_AaaS_Factory/pull/37

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

## [v1.3.10] - 2026-01-08

### Added
- Repo-level fail-fast lock for OpenPR execution (`refs/heads/__factory_lock__/open_pr`)
- Minimal PR scheduler to prevent concurrent Factory PR creation on the same base branch (fail-fast, no wait/retry)

### Changed
- Integrate PR scheduler check before RepoLock acquisition in `open_pr_cli.py`

### Tests
- Add unit tests for PR scheduler blocking and fail-safe behavior
- Add/extend unit tests for RepoLock acquire/release behavior

---

## [v1.3.9] - 2026-01-08

### Added
- Repo-level fail-fast lock for OpenPR execution (`refs/heads/__factory_lock__/open_pr`)
- Minimal PR scheduler to prevent concurrent Factory PR creation on the same base branch (fail-fast, no wait/retry)

### Changed
- Integrate PR scheduler check before RepoLock acquisition in `open_pr_cli.py`

### Tests
- Add unit tests for PR scheduler blocking and fail-safe behavior
- Add/extend unit tests for RepoLock acquire/release behavior

---

## [v1.3.8] - 2026-01-08

### Changed
- Align documentation with evidence-based current state of the Factory.
- Clarify that the Factory is a fully automated Release Factory, while parallel AaaS development is not yet implemented.
- Formalize the semi-automated Factory self-development protocol (Task Brief → VS Code / Copilot → PR → Human Gate) in documentation.
- Remove any ambiguity between implemented capabilities and design-only future features.

### Docs
- Update README.md to reflect authoritative current operational status.
- Update Factory master documents to clearly separate decision and execution layers.
- Normalize Factory Automation Master v10 to match actual implementation status.

---

## [v1.3.7] - 2026-01-06

### Changed
- Skip the GitHub Actions release workflow on bot-triggered tag pushes (prevents loops/duplicate runs).
- Stabilize the fully automated release flow by ensuring the release job runs only for human-created tags.

---

## [v1.3.6] - 2026-01-06

### Changed
- Final verification of release workflow

---

## [v1.3.5] - 2026-01-06

### Changed
- Verify restored release workflow

---

## [v1.3.2] - 2026-01-06

### Changed
- Deduplicate release note separators and SSOT section generation

---

## [v1.3.1] - 2026-01-06

### Changed
- Test release automation: GitHub Release body is generated from CHANGELOG.md section

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
- **CLI JSON outputs**
  - All relevant CLI commands now include `contractVersion` and `ssotDocument` fields.
  - Error codes and reasons are standardized for machine readability.

### Security
- Preserved fail-safe semantics: GitHub authorization failures never strand users.
- Approval token validation is enforced before any write-side effects.

### Backward Compatibility
- v1.2 workflows remain supported.
- JSON output changes are additive and non-breaking.

---

## [v1.2.0]
- Initial Open-PR Contract with human approval gating.
- ToolGate-based permission checks for controlled Git operations.
- (smoketest) changelog automerge
<--exclude smoketest 2026-01-10-06:45:39 -->
