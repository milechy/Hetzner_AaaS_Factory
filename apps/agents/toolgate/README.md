# ToolGate (v1.0)

Policy Engine for tool execution permissioning.
- blockedWhen -> allowedWhen -> default-deny
- optional Bearer auth via TOOLGATE_API_KEY
- policies loaded from TOOLGATE_POLICIES_DIR (default: ./policies)

## Run
```bash
cd apps/agents/toolgate
export TOOLGATE_POLICIES_DIR="policies"
# optional:
# export TOOLGATE_API_KEY="change-me"
uvicorn toolgate.main:app --host 0.0.0.0 --port 8088

Example

POST /v1/evaluate

{
  "policyVersion": "toolgate_v1",
  "requestId": "req_123",
  "proposalId": "prp_abc",
  "tool": "run_tests",
  "effect": "validate",
  "context": {
    "humanApproved": false,
    "riskLevel": "low",
    "highRiskDetected": false,
    "pathsTouched": ["README.md"],
    "filesTouchedCount": 1,
    "domains": ["agent"]
  }
}

---

## 次にやること（接続）
AgentBuilderAgent v1.0 側の環境変数を設定してください。

```bash
export TOOLGATE_URL="http://localhost:8088"
# ToolGateにAPIキーを設定した場合のみ
export TOOLGATE_API_KEY="change-me"