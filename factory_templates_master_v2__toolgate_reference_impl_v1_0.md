# factory_templates_master_v2__toolgate_reference_impl_v1_0.md
AaaS Factory – Templates Master Addendum (ToolGate Reference Implementation v1.0)
最終更新: 2025-12-24

---

## 0. 目的
Agent が tool 実行可否を判断しない構造を保証するため、
ToolGate（Policy Engine）の最小リファレンス実装を Factory テンプレとして標準化する。

v1.0 の要件：
- API: POST /v1/evaluate
- 評価順: blockedWhen → allowedWhen → default-deny
- 監査ログ: tool/decision/reason/policyVersion/requestId/proposalId
- Auth: 任意（TOOLGATE_API_KEY がある場合のみ Bearer 必須）
- Policy: YAML/JSON ロード（例: policies/toolgate_v1.yaml）

参照SSOT：
- master__tool_gate_policy_v1.md
- master__tool_gate_policy_v1__api_contract_v1_0.md

---

## 1. 標準ディレクトリ（推奨）
モノレポ配置：
- apps/agents/toolgate/

単体リポでも可。

---

## 2. ファイルツリー（SSOT）
apps/agents/toolgate/
├─ pyproject.toml
├─ README.md
├─ toolgate/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ models.py
│  ├─ policy.py
│  ├─ evaluator.py
│  └─ audit.py
└─ policies/
   └─ toolgate_v1.yaml

---

## 3. 実装要点（必須）

### 3.1 Evaluate API（/v1/evaluate）
- Request:
  - policyVersion
  - requestId / proposalId(optional)
  - tool / effect(read|validate|write)
  - context(humanApproved, riskLevel, highRiskDetected, pathsTouched, filesTouchedCount, domains)
- Response:
  - decision(allow|deny)
  - reason
  - policyVersion

### 3.2 評価順（厳守）
1) blockedWhen（pathsPrefix 等）に一致 → deny
2) tool+effect で rule を見つけ、allowedWhen 満たす → allow（満たさない → deny）
3) rule が無ければ → deny（default-deny）

### 3.3 監査ログ（必須）
出力/保存手段は実装側で選べるが、以下を必ず残す：
- ts
- requestId
- proposalId
- tool
- effect
- decision
- reason
- policyVersion

---

## 4. Policy（例：toolgate_v1.yaml）
- blockedWhen.pathsPrefix は high-risk prefix をデフォルト拒否として持つ
- v1.0 は read/validate を許可、write は（運用上）deny を推奨
- v1.2 以降で create_branch / create_pull_request を human gate 付きで解禁

---

## 5. 接続（Agent側）
Agent（例: AgentBuilderAgent v1.0）は Tool 実行前に ToolGate を呼び、allow のときのみ実行する。
deny の場合は proposal を継続し、deny reason を summary に記載する。

必須環境変数（例）：
- TOOLGATE_URL
- TOOLGATE_API_KEY（任意）

---

# END