# Changelog

All notable changes to this project are documented in this file.
This project follows a contract-first approach for controlled Git operations.

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