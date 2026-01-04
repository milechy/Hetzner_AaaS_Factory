# master__tool_gate_policy_v1.md
AaaS Factory – ToolGate Policy Master (v1)
最終更新: 2025-12-24

---

## 0. 目的
Tool（実行権限）の解禁条件を **Policy としてSSOT化**し、
Agent が越権（自己判断で実行）しない構造を保証する。

---

## 1. 原則
- Agent は tool 実行の可否を判断しない
- ToolGate（Policy Engine）が判断する
- high-risk（infra/security/billing/template）はデフォルト拒否
- Human Approval を “実行境界” として扱う

---

## 2. Policy Schema（概略）
```json
{
  "tool": "create_pull_request",
  "effect": "write",
  "allowedWhen": {
    "humanApproved": true,
    "riskLevel": ["low"],
    "highRiskDetected": false,
    "maxFilesTouched": 10,
    "allowedDomains": ["agent", "web", "api"]
  },
  "blockedWhen": {
    "pathsPrefix": ["infra/", "ops/", ".github/", "templates/", "security/", "billing/"]
  }
}

⸻

## 3. v1 推奨ポリシー（初期値）

3.1 Read-only tools（常時許可）
- read_repo
- schema_validate
- proposal_validate
- github_read（v1.1以降）
- artifact_read（v1.1以降）

条件：
- humanApproved 不要
- riskLevel 不問（ただし secret を扱う出力は禁止）

3.2 Validate tools（常時許可）
- git_diff（ローカル/仮想差分）
- ci_check（読み取り/検証のみ）
- run_tests（sandbox 実行のみ）

条件：
- humanApproved 不要
- 実行対象は “workspace/sandbox” に限定

3.3 Write tools（v1.2 条件付き）
- create_branch
- create_pull_request

必須条件：
- humanApproved = true
- highRiskDetected = false
- touchedFiles <= 10（初期値）
- blocked prefixes を含まない

禁止：
- merge / push / apply / deploy（v1では禁止）

⸻

## 4. ログ要件（監査）

ToolGate は以下を必ず記録（実装側要件）：
- tool name
- decision（allow/deny）
- reason
- policy version
- requestId / proposalId

⸻

END