# SelfDevAgent — Best Practices v3  
Planning Module v3 / Orchestration-Aware Edition  
最終更新: 2025-11-19

---

# 0. 目的

SelfDevAgent は AaaS Factory の中枢エージェントであり、  
Factory 自身の改善サイクルを自動で駆動する。

v3 では Orchestrator 系モデルの知見を取り込み、

- Intent Normalization
- Adaptive Planning（深さを可変にする）
- Multi-Agent Routing（適切な子エージェントの選択）
- Risk-aware / Cost-aware Planning
- Review → Reflection の強化

という **「深い推論とマルチエージェント協調」** を実装する。

本ドキュメントは SelfDevAgent の完全な行動規範（SSOT）である。

---

# 1. SelfDevAgent の 5 層構造（v3）

SelfDevAgent v3 は以下の 5 層で構成される：

1. **Intent Layer（Intent Engine v2）**  
2. **Planner Layer（Planning Module v3）**  
3. **Executor Layer（Tool / Agent Caller）**  
4. **Reviewer Layer（Self-Check / Multi-Judge）**  
5. **Reflector Layer（Reflection / Adaptive Retry）**

Factory の全自動化タスクはこの 5 層を順に流れる。

---

# 2. Intent Layer（Intent Engine v2）

Intent Layer の役割：

- ユーザーの自然言語要求から Intent Object を生成
- Rewrite → Decompose → Interpret → Validate の多段階 pipeline
- Factory の master__* に照らして矛盾・危険性を検知
- Plan の精度を最大化するため「構造化 Intent」を出す

Intent Object の構造：

```json
{
  "goal": "string",
  "sub_intents": [],
  "entities": [],
  "actions": [],
  "constraints": [],
  "ui_flows": [],
  "dataflows": [],
  "affected_files": [],
  "related_master_sections": []
}
````

Intent Layer は v2（既に定義済み）をそのまま使用。

---

# 3. Planner Layer v3（本ドキュメントの主題）

Planner v3 の特徴：

* **Adaptive Depth Planning（深さ1/2/3 の動的切り替え）**
* **Multi-Agent Routing（GraphEditorAgent / TemplateAgent などへ適切に分配）**
* **Risk-aware / Cost-aware Planning（変更規模と危険度で step を最適化）**
* **Master-aware Planning（API/DB/UI/Infra の SSOT との整合）**

## 3.1 Planning Depth（v3）

Planner は Intent と context から自動で depth を決定する：

| Depth | 対応範囲                                   |
| ----- | -------------------------------------- |
| 1     | 軽微な修正（2ファイル以内／Graph非変更）                |
| 2     | 中規模（API/DB/UI の調整、Graphは軽微）            |
| 3     | 大規模（Template更新／Graph構造変更／Factory全体に影響） |

depth=3 の場合は必ず Reviewer Layer の強化が挿入される。

## 3.2 Plan の構造

```ts
type PlanStepType =
  | "READ_MASTER"
  | "READ_CODE"
  | "ANALYZE_DIFF"
  | "GENERATE_SPEC"
  | "GENERATE_CODE"
  | "UPDATE_GRAPH"
  | "UPDATE_TEMPLATE"
  | "RUN_TESTS"
  | "WRITE_DOCS"
  | "OPEN_PR";
```

Plan は以下を含む：

```ts
type PlanStep = {
  id: string;
  type: PlanStepType;
  description: string;
  target_files: string[];
  tools: string[];        // 呼び出す Agent / Tool
  depends_on: string[];
  risk: "low" | "medium" | "high";
  cost_estimate: number;  // 相対スコア
};

type Plan = {
  goal: string;
  steps: PlanStep[];
  estimated_cost: number;
  depth_level: 1 | 2 | 3;
};
```

## 3.3 エージェントルーティング（Multi-Agent Routing）

Planner v3 は、各 step に最適なエージェントを自動選択する。

| Step            | Routing Agent                                 |
| --------------- | --------------------------------------------- |
| READ_MASTER     | SelfDevAgent (internal)                       |
| ANALYZE_DIFF    | SelfDevAgent                                  |
| GENERATE_SPEC   | SpecSyncAgent                                 |
| GENERATE_CODE   | WebDevAgent / BackendDevAgent / SwiftDevAgent |
| UPDATE_TEMPLATE | TemplateAgent                                 |
| UPDATE_GRAPH    | GraphEditorAgent                              |
| RUN_TESTS       | CICDAgent                                     |
| WRITE_DOCS      | SelfDevAgent                                  |
| OPEN_PR         | SelfDevAgent + GitHub API wrapper             |

Planner v3 は LangGraph 的に「Agent の遷移計画」を生成する。

## 3.4 Risk-aware / Cost-aware Planning

Planner v3 は以下のルールを持つ：

* **risk=high** を含む場合 → Reflection Layer が自動的に強化
* **cost_estimate > budget** のとき
  → depth を自動で下げる／Plan を2つに分割
* Graph と Template の変更は常に high-risk と扱う
* Plan に “危険ノード” がある場合
  → 追加 reviewer（multi-judge）を必須にする

---

# 4. Executor Layer（v3）

Executor は Planner で生成した step を順番に実行する。

特徴：

* 可能な限り parallel 実行
* 依存関係は planner が保証
* Agent 呼び出しは LangGraph runtime に委譲
* 実行ログはすべて home-rag の「factory-action-log」に蓄積

---

# 5. Reviewer Layer（v3）

Planner v3 の導入により Reviewer も強化。

Reviewer のルール：

1. **Spec-to-Plan 整合性チェック**
2. **Plan-to-Implementation 整合**
3. **Master Drift Check**
4. **Graph Safe-Mode Check**（GraphEditorAgentが壊していないか）
5. **Template Consistency Check**（template drift）

さらに v3 では：

* **Multi-Judge（複数 LLM でのレビュー）**
* **Rubric-based scoring（評価表に沿った点数付け）**
* **Risk-aware review depth**（Plan の risk に応じてチェック項目が増減）

---

# 6. Reflector Layer（v3）

Reflection（再推論）は最大 **2回** 行う。

Reflection が走る条件：

* Reviewer が “重大矛盾” を検出
* Plan と Intent の mismatch
* Template drift が見つかった
* Graph 構造が破損の可能性
* PR 提案が品質スコア60以下

Reflection の動作：

1. Intent を再評価
2. Planner v3 をもう一度実行（深さを変更する場合あり）
3. 改善された Plan に基づき再度 Executor に流す

---

# 7. SelfDevAgent の Input/Output（v3）

## 7.1 入力

```ts
type SelfDevInput = {
  request: string;
  context_files?: string[];
  force_depth?: 1 | 2 | 3;
};
```

## 7.2 出力

```ts
type SelfDevOutput = {
  plan: Plan;
  pr_proposal: PullRequestProposal;
  logs: string[];
  reflection_count: number;
  quality_score: number;
};
```

---

# 8. 失敗パターンとガードレール（v3）

SelfDevAgent は以下の “failure mode” を常にチェックする：

* Plan が浅すぎる
* Plan が深すぎる（過剰設計）
* Graph が壊れる変更
* Template の drift
* API/DB に整合しない変更
* UI キットと一致しない UI 誘導
* SaaS Structure Master と矛盾した page 追加

すべて Planner（risk-aware）→ Reviewer（multi-judge）→ Reflection（2回まで）で吸収する。

---

# 9. 連携するマスター

SelfDevAgent v3 は以下の master__* を参照する：

* factory_master_v1
* factory_automation_master_v8
* infra_master_v2
* api_standards_master_v1
* design_system_master_v1
* data_modeling_master_v1
* saas_structure_master_v1
* ui_kit_master_v1
* agent_specs_master_v1
* agent_roles_master_v1
* billing_options_master_v1
* x402_billing_option_spec_v1
* selfdevagent_best_practices_v2（旧版）

SelfDevAgent v3 は、旧 v2 仕様を完全上位互換として統合する。

---

# 10. 今後の拡張（v4 プレビュー）

* Machine-learned routing（成功ログから最適エージェント選択を学習）
* Planner tree（Plan を木構造にして並列化）
* Graph Structure Prediction（GraphEditorAgent の予測モデル）
* Template Impact Prediction（テンプレ壊れる前の予測）

---

# END

```

---