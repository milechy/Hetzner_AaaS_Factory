# controlled_git Contract Implementation

## Module: controlled_git/cli.py

### Commands
- `policy-check`: Validate proposal against policy
- `approve`: Issue approval token
- `verify-token`: Verify token signature/expiry
- `open-pr`: Create PR (with fail-safe)
- `contract`: Show SSOT linkage metadata

### Key Functions

#### canonical_proposal_hash(proposal: dict) -> str
```python
minimal = {
  "metadata": {
    "repo": ...,
    "baseBranch": ...,
    "proposalId": ...,
    "title": ...
  },
  "changes": {
    "files": [{"path": ..., "patch": ...}]
  }
}
return "sha256:" + sha256(stable_json(minimal))
```

#### verify_token(token: dict, secret: str) -> (bool, str)
1. Verify HMAC-SHA256 signature
2. Check expiresAt (ISO-8601)
3. Optional: Check revocation list
4. Return (ok, code)

#### _require_scope(token, repo, base, action, actor)
1. repo match
2. baseBranch match
3. action in actions
4. actorId match (mandatory v1.3)

### Error Codes (v1.3)
- APPROVAL_INVALID_SIGNATURE
- APPROVAL_EXPIRED
- APPROVAL_REVOKED
- APPROVAL_ACTOR_MISMATCH
- APPROVAL_SCOPE_MISMATCH
- GITHUB_401
- GITHUB_403_* (PAT_RESOURCE_NOT_ACCESSIBLE, ORG_POLICY, etc.)
- GITHUB_422_ALREADY_EXISTS

### Machine-Readable Output (--json)
```json
{
  "ok": true/false,
  "status": "opened"/"fallback"/"...",
  "code": "OK"/"ERROR_CODE",
  "contractVersion": "v1.3",
  "ssotDocument": "master__open_pr_contract_v1_3.md",
  ...
}
```
