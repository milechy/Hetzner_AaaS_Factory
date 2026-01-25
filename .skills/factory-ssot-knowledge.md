# Factory SSOT Knowledge

## What is Factory?
- **Factory**: AI development orchestration SDK
- **Not**: A SaaS product
- **Purpose**: Control who/what/when can develop (safely)

## SSOT Hierarchy
1. **master__open_pr_contract_v1_3.md**: PR creation contract (highest priority)
2. **master__factory_master_v3.md**: Factory positioning & phases
3. **Implementation**: controlled_git/, tools/

SSOT takes precedence over:
- CLI behavior
- ToolGate policy
- Agent heuristics
- README

## v1.3 Contract Key Points

### Hard Requirements (ALL must be satisfied)
1. humanApproved == true
2. Valid Approval Token
3. Token signature valid + not expired
4. actorId match (mandatory-by-default v1.3)
5. ToolGate returns allow
6. No high-risk paths

### Approval Token Contract
- Type: JWT-like (HMAC-SHA256 signature)
- Scope: repo/baseBranch/proposalHash/actorId
- Expiry: ISO-8601 timestamp
- Revocation: optional (APPROVAL_REVOCATION_LIST_PATH)

### Actor Binding (v1.3)
- actorId is opaque string
- Source priority: --actor > CG_ACTOR > GITHUB_ACTOR
- Missing/mismatch → 403-equivalent denial
- Numeric strings (e.g. "12345") permitted but discouraged

### Fail-Safe Guarantee
- GitHub 401/403 MUST NOT abort
- Return fallback URL: https://github.com/{repo}/pull/new/{head}
- Classification is best-effort (not a hard dependency)

## Development Phases (SSOT)
- Phase 0: Scope/Policy Lock
- Phase 1: Task Intake
- Phase 2: Plan
- Phase 3: Implement
- Phase 4: Verify
- Phase 5: Review
- Phase 6: Proposal/PR
- Phase 7: Human Approval
- Phase 8: Apply/Post-merge (human-driven merge only)

## Current Milestone
External repo safe PR creation (proposal-only)

## What Factory Does NOT Do
- Auto-merge PRs
- Develop itself autonomously (human-driven)
- Bypass human approval
