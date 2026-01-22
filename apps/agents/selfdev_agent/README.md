# SelfDevAgent v4 (MVP)

Status: PLANNED (v1.6.0) – proposal-only MVP

Loop:
Plan (read-only) -> Exec (writer) -> Verify -> Review (reviewer) -> PR Proposal payload

Hard constraints (SSOT):
- Writer = Codex (workspace write + run_* allowed)
- Reviewer = Opus 4.5 (read-only only; any write-side effect must fail-fast)
- All model calls MUST go through LLMRouter with profile=writer|reviewer
- MVP must NOT create PRs (proposal-only). OpenPR boundary remains the only write pipeline.
