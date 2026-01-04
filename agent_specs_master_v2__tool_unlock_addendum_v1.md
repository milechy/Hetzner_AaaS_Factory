# agent_specs_master_v2__tool_unlock_addendum_v1.md
AaaS Factory – Agent Specs Addendum (Tool Unlock v1)
最終更新: 2025-12-24

---

## 0. 目的
Agent Specs v2（SSOT）に対して、v1（限定 Tool 解禁）を追補し、
AgentBuilderAgent を含む Agent プロジェクトの進化パスを統一する。

---

## 1. v1 段階（参照）
- master__tool_unlock_roadmap_v1.md

---

## 2. 追加ルール（厳守）

### 2.1 Agent は Tool 解禁判断を行わない
- Agent は「Tool利用提案」＋「根拠」＋「期待効果」のみを出す
- 実行可否は ToolGate Policy に委譲する

参照：
- master__tool_gate_policy_v1.md

### 2.2 Safe Tools（v1.0）
- read_repo / schema_validate / proposal_validate / git_diff / ci_check / run_tests（sandbox）
- write 系は依然禁止

### 2.3 Write Tools（v1.2）
- create_branch / create_pull_request は **humanApproved=true** 必須
- highRiskDetected=true の場合は deny（初期値）

---

## 3. AgentBuilderAgent の v1 進化
- v0：proposal-only
- v1.0：既存ツリー（repoContext.existingTree）を読み、差分精度を向上
- v1.1：GitHub read を統合し、競合/CI結果を考慮
- v1.2：human gate のもとで PR 作成まで（ただし merge 禁止）

---

# END