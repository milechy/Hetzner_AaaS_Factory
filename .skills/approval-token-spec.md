# Approval Token Specification

## Structure
```json
{
  "id": "uuid",
  "issuedAt": "ISO-8601",
  "issuedBy": "human",
  "scope": {
    "repo": "owner/repo",
    "baseBranch": "main",
    "proposalHash": "sha256:...",
    "expiresAt": "ISO-8601",
    "actions": ["prepare_branch", "apply_patch", "open_pr"],
    "actorId": "milechy"
  },
  "signature": "hmac-sha256:..."
}
```

## Signature Algorithm
```python
payload = {k: v for k, v in token.items() if k != "signature"}
message = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
signature = hmac.sha256(secret, message).hexdigest()
token["signature"] = "hmac-sha256:" + signature
```

## Validation Rules
1. Signature MUST match (hmac.compare_digest)
2. expiresAt MUST be future timestamp
3. scope.repo MUST match target repo
4. scope.baseBranch MUST match target branch
5. scope.proposalHash MUST match canonical_proposal_hash
6. scope.actorId MUST match runtime actor (v1.3 mandatory)

## Actor Binding (v1.3)
- actorId is opaque string
- Runtime source: --actor > CG_ACTOR > GITHUB_ACTOR
- Missing → APPROVAL_ACTOR_MISSING
- Mismatch → APPROVAL_ACTOR_MISMATCH (403-equivalent)

## Revocation (Optional)
- Path: APPROVAL_REVOCATION_LIST_PATH
- Format: JSON array ["id1", "id2"] or JSONL
- Revoked token → APPROVAL_REVOKED
