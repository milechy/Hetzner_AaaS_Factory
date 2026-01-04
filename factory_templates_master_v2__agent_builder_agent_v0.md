# factory_templates_master_v2__agent_builder_agent_v0.md
AaaS Factory – Templates Master Addendum (AgentBuilderAgent v0)
最終更新: 2025-12-24

---

## 0. 目的
AgentBuilderAgent v0（OpenAI Agents SDK ベース）を
Spec(YAML/JSON) → skeleton生成 → PullRequestProposal(JSON)
まで実行し、提案で停止する標準テンプレを定義する。

v0 制約：
- git write / push / merge / 実PR作成はしない
- infra change / secret 操作はしない
- LLM は必ず LLMRouter 経由、Agent は profile のみ指定
- high-risk（infra/security/billing/template）は v0 対象外
  - 検出は行う
  - skeleton は生成してよい
  - high-risk file は生成しない（changes.files から除外）

---

## 1. 標準ディレクトリ
推奨配置（モノレポ）：
- apps/agents/agent-builder-agent/

単体リポでも可。

---

## 2. ファイルツリー（SSOT）
apps/agents/agent-builder-agent/
├─ pyproject.toml
├─ README.md
├─ agent_builder_agent/
│  ├─ __init__.py
│  ├─ agent.py
│  ├─ cli.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ errors.py
│  │  ├─ proposal_builder.py
│  │  ├─ risk_detector.py
│  │  ├─ skeleton_generator.py
│  │  └─ spec_parser.py
│  ├─ router/
│  │  ├─ __init__.py
│  │  └─ llm_router_client.py
│  └─ schemas/
│     ├─ __init__.py
│     ├─ agent_builder_error_v0.py
│     ├─ agent_builder_request_v0.py
│     └─ pull_request_proposal_v0.py
└─ tests/
   ├─ test_high_risk_filtering.py
   └─ test_parse_and_propose.py

---

## 3. 実装要点（必須）

### 3.1 入力・出力（v0 contract）
- 入力: AgentBuilderRequestV0
- 出力: PullRequestProposalV0 または AgentBuilderErrorV0
- Schema SSOT:
  - schemas__agent_builder_request_v0.json
  - schemas__pull_request_proposal_v0.json
  - schemas__agent_builder_error_v0.json

### 3.2 steps の扱い（柔軟）
- spec 内で `name` / `purpose` のみ必須
- `steps` は無くてもよい（Routerで推論補完）

### 3.3 High-risk 検出時の挙動（合意済み）
- skeleton は生成して良い
- ただし high-risk path（infra/, ops/, .github/, templates/, security/, billing/）は
  - changes.files へ入れない
- risk.highRiskDetected=true、notes に根拠
- manualSteps に human gate を要求

### 3.4 LLMRouter 境界
- Agent が指定するのは profile のみ
- modelId は Router 内部の責務（Agent 側で保持/ログ出ししない）

---

## 4. Router endpoint 契約（参照SSOT）
本テンプレは Router API 契約 SSOT を参照する：
- master__llm_router_api_contract_v1.md

---

## 5. 最小テスト（必須）
- spec normalize（name/purpose 必須）
- high-risk キーワード検出
- high-risk path フィルタ

---

## 6. E2E Examples（v0・proposal-only）

### 6.1 Minimal Request（steps なし）
```json
{
  "requestId": "req_example_min",
  "specFormat": "json",
  "specObject": {
    "name": "Example Agent",
    "purpose": "Generate a proposal-only skeleton."
  },
  "target": {
    "repoKind": "single",
    "language": "python",
    "framework": "agents-sdk",
    "runtime": "python311"
  },
  "routingProfile": "codegen_standard"
}

6.2 Normal Proposal（highRiskDetected=false）
	•	risk.level = low
	•	changes.files に skeleton が含まれる
	•	manualSteps は空

（※ 完全例は examples/response.sample.json を参照）

⸻

6.3 High-risk Request（billing を含む）

{
  "requestId": "req_example_highrisk",
  "specFormat": "yaml",
  "specText": "name: Billing Agent\npurpose: Propose only.\ndomains: [billing]\n"
}

6.4 High-risk Proposal の特徴
	•	risk.highRiskDetected = true
	•	risk.level = high
	•	changes.files に billing / infra / security / template 配下のファイルは含まれない
	•	validation.manualSteps に human gate が必ず入る

⸻

END