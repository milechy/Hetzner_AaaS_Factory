# master__tool_gate_policy_v1__api_contract_v1_0.md
AaaS Factory – ToolGate API Contract (v1.0)
最終更新: 2025-12-24

---

## 0. 目的
Agent が tool 実行の可否を判断しない構造を保証するため、
ToolGate（Policy Engine）の最小 API 契約をSSOTとして定義する。

参照：
- master__tool_gate_policy_v1.md

---

## 1. API（最小）

### 1.1 Evaluate
- Method: POST
- Path: /v1/evaluate
- Content-Type: application/json

#### Request（例）
```json
{
  "policyVersion": "toolgate_v1",
  "requestId": "req_20251224_0001",
  "proposalId": "prp_optional",
  "tool": "run_tests",
  "effect": "validate",
  "context": {
    "humanApproved": false,
    "riskLevel": "low",
    "highRiskDetected": false,
    "pathsTouched": ["README.md", "agent_builder_agent/agent.py"],
    "filesTouchedCount": 2,
    "domains": ["agent"]
  }
}

Response（例）

{
  "decision": "allow",
  "reason": "validate tools allowed without human approval",
  "policyVersion": "toolgate_v1"
}

2. 評価順（必須）
 1. blockedWhen（pathsPrefix 等）に一致 → deny
 2. allowedWhen 条件を満たす → allow
 3. その他 → deny（default deny）

⸻

3. 監査ログ（必須）

ToolGate は次を必ず記録/返却できること：
- tool
- decision
- reason
- policyVersion
- requestId
- proposalId（あれば）

⸻

END