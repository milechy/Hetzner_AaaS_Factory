# Summary
<!-- What is changed and why? Keep it concise. -->

## Scope
- [ ] SSOT (master__open_pr_contract_v1_3.md)
- [ ] CLI (controlled_git/cli.py)
- [ ] ToolGate (apps/agents/toolgate)
- [ ] Other (describe below)

# Key Changes
## SSOT
- [ ] SSOT updated and consistent (no duplicated/contradicting sections)
- [ ] SSOT ↔ CLI linkage specified (contractVersion/ssotDocument)

## CLI
- [ ] `python -m controlled_git.cli contract --json` implemented
- [ ] All `--json` outputs include:
  - `contractVersion` (e.g., `v1.3`)
  - `ssotDocument` (e.g., `master__open_pr_contract_v1_3.md`)
- [ ] GitHub API Base URL guarded (fallback to default + audit warning)
- [ ] 401/403 fail-safe fallback guaranteed (reason classification best-effort only)
- [ ] actorId mismatch denies (mandatory-by-default)

## ToolGate
- [ ] write-effect requires non-empty `pathsTouched`
- [ ] `pathsTouched` rejects absolute paths, `..` segments
- [ ] `filesTouchedCount == unique(pathsTouched)` enforced
- [ ] deny reason strings are stable (grep/monitoring friendly)

# Backward Compatibility
- [ ] v1.2 valid flows continue to work
- [ ] JSON output adds fields but does not break existing keys

# Manual Verification (No CI Required)
## Contract metadata
- [ ] `python -m controlled_git.cli contract --json` returns v1.3 linkage

## Approval token
- [ ] Expired token yields `APPROVAL_EXPIRED`
- [ ] Revoked token yields `APPROVAL_REVOKED`
- [ ] Actor mismatch yields `APPROVAL_ACTOR_MISMATCH`

## GitHub fail-safe fallback
- [ ] 401/403 yields `ok=true`, `status=fallback`, and `prCreateUrl` (classification is best-effort)

## ToolGate boundaries
- [ ] write-effect + empty `pathsTouched` => deny
- [ ] absolute path => deny
- [ ] `..` segment => deny
- [ ] mismatch `filesTouchedCount` => deny

# Notes / Follow-ups
<!-- Add any operational notes, rollout notes, or known limitations. -->
