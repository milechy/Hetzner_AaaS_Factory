# Changelog

All notable changes to this project are documented in this file.
This project follows a contract-first approach for controlled Git operations.

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