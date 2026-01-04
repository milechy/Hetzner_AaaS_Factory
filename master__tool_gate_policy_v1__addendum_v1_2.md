# master__tool_gate_policy_v1__addendum_v1_2.md
AaaS Factory – ToolGate Policy Master (v1) Addendum (v1.2 Limited Write)
最終更新: 2025-12-24

---

## 0. 目的
ToolGate における v1.2 限定write（create_branch / create_pull_request）の許可条件をSSOT化する。
評価順（blockedWhen → allowedWhen → default-deny）は不変。

参照：
- master__tool_gate_policy_v1.md
- master__tool_gate_policy_v1__addendum_v1_1.md
- master__tool_gate_policy_v1__api_contract_v1_0.md

---

## 1. v1.2 write tools（最小）
- create_branch（effect=write）
- create_pull_request（effect=write）

禁止（v1.2）：
- merge / rebase / force-push
- PR comment / label の更新
- apply / deploy / infra

---

## 2. allow 条件（必須 AND）
- humanApproved: true 必須（外部入力のみ）
- riskLevel: low のみ
- highRiskDetected: false 必須
- maxFilesTouched: <= 10（推奨。ポリシーで調整可）
- blockedWhen.pathsPrefix に抵触しない
- ルール未一致は deny（default-deny）

---

## 3. 監査ログ（v1.2 追加推奨）
ToolGate の audit には以下を含める：
- approvedBy / approvedAt（存在する場合）
- proposalId
- filesTouchedCount
- tool/effect/decision/reason/policyVersion

※ approvedBy/approvedAt は「監査用途」。判定条件は humanApproved を主とする。

---

## 4. ポリシー実装ガイド（例）
- tool: create_branch, effect: write
  allowedWhen:
    humanApproved: [true]
    riskLevel: ["low"]
    highRiskDetected: [false]
    maxFilesTouched: 10

- tool: create_pull_request, effect: write
  allowedWhen:
    humanApproved: [true]
    riskLevel: ["low"]
    highRiskDetected: [false]
    maxFilesTouched: 10

---

## 5. 検証用リクエスト例（curl / Postman）

### 5.1 前提
- Endpoint: POST {TOOLGATE_URL}/v1/evaluate
- Optional Auth: Authorization: Bearer {TOOLGATE_API_KEY}
- policyVersion: toolgate_v1（テンプレ toolgate_v1.yaml を想定）
- v1.2 write 対象：create_branch / create_pull_request
- blockedWhen.pathsPrefix（deny）：
  - infra/ ops/ .github/ templates/ security/ billing/

以下は curl 例（TOOLGATE_API_KEY を使わない場合は Authorization ヘッダを外す）。

---

### 5.2 Scenario 7: humanApproved=false → deny（no-call 想定）
```bash
curl -sS -X POST "$TOOLGATE_URL/v1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOOLGATE_API_KEY" \
  -d '{
    "policyVersion": "toolgate_v1",
    "requestId": "req_12345678",
    "proposalId": "prp_demo_v12",
    "tool": "create_branch",
    "effect": "write",
    "context": {
      "humanApproved": false,
      "riskLevel": "low",
      "highRiskDetected": false,
      "pathsTouched": ["src/app.py"],
      "filesTouchedCount": 1,
      "domains": ["agent"]
    }
  }'

期待：decision=deny

curl -sS -X POST "$TOOLGATE_URL/v1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOOLGATE_API_KEY" \
  -d '{
    "policyVersion": "toolgate_v1",
    "requestId": "req_12345678",
    "proposalId": "prp_demo_v12",
    "tool": "create_branch",
    "effect": "write",
    "context": {
      "humanApproved": true,
      "riskLevel": "low",
      "highRiskDetected": false,
      "pathsTouched": ["src/app.py","src/lib/util.py"],
      "filesTouchedCount": 2,
      "domains": ["agent"]
    }
  }'

期待：decision=allow

5.4 Scenario 8: filesTouchedCount > maxFilesTouched → deny

（maxFilesTouched=10 の場合）

curl -sS -X POST "$TOOLGATE_URL/v1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOOLGATE_API_KEY" \
  -d '{
    "policyVersion": "toolgate_v1",
    "requestId": "req_12345678",
    "proposalId": "prp_demo_v12",
    "tool": "create_branch",
    "effect": "write",
    "context": {
      "humanApproved": true,
      "riskLevel": "low",
      "highRiskDetected": false,
      "pathsTouched": ["src/0.py","src/1.py","src/2.py","src/3.py","src/4.py","src/5.py","src/6.py","src/7.py","src/8.py","src/9.py","src/10.py"],
      "filesTouchedCount": 11,
      "domains": ["agent"]
    }
  }'

期待：decision=deny

5.5 Scenario 9: blockedWhen.pathsPrefix 該当 → deny

curl -sS -X POST "$TOOLGATE_URL/v1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOOLGATE_API_KEY" \
  -d '{
    "policyVersion": "toolgate_v1",
    "requestId": "req_12345678",
    "proposalId": "prp_demo_v12",
    "tool": "create_pull_request",
    "effect": "write",
    "context": {
      "humanApproved": true,
      "riskLevel": "low",
      "highRiskDetected": false,
      "pathsTouched": ["infra/main.tf"],
      "filesTouchedCount": 1,
      "domains": ["agent"]
    }
  }'

期待：decision=deny（blockedWhen による）

5.6 Scenario 9’: highRiskDetected=true → deny

curl -sS -X POST "$TOOLGATE_URL/v1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOOLGATE_API_KEY" \
  -d '{
    "policyVersion": "toolgate_v1",
    "requestId": "req_12345678",
    "proposalId": "prp_demo_v12",
    "tool": "create_pull_request",
    "effect": "write",
    "context": {
      "humanApproved": true,
      "riskLevel": "low",
      "highRiskDetected": true,
      "pathsTouched": ["src/app.py"],
      "filesTouchedCount": 1,
      "domains": ["agent"]
    }
  }'

期待：decision=deny（highRiskDetected による）

5.7 create_pull_request allow 例（Scenario 6 のPR版）

curl -sS -X POST "$TOOLGATE_URL/v1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOOLGATE_API_KEY" \
  -d '{
    "policyVersion": "toolgate_v1",
    "requestId": "req_12345678",
    "proposalId": "prp_demo_v12",
    "tool": "create_pull_request",
    "effect": "write",
    "context": {
      "humanApproved": true,
      "riskLevel": "low",
      "highRiskDetected": false,
      "pathsTouched": ["src/app.py"],
      "filesTouchedCount": 1,
      "domains": ["agent"]
    }
  }'

期待：decision=allow

⸻

5.8 Postman 最小テンプレ
- Method: POST
- URL: {{TOOLGATE_URL}}/v1/evaluate
- Headers:
- Content-Type: application/json
- Authorization: Bearer {{TOOLGATE_API_KEY}}（任意）
- Body: raw JSON（上記のいずれか）

⸻

END