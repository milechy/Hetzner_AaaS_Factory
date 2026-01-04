# agent_specs_master_v2__tool_unlock_addendum_v1__detailed_v1_0.md
AaaS Factory – Agent Specs Addendum (Tool Unlock v1) Detailed (v1.0)
最終更新: 2025-12-24

---

## 0. 目的
agent_specs_master_v2__tool_unlock_addendum_v1.md を補完し、
v1.0での Agent 実装要件（ToolGate/検証/差分寄せ）を明確化する。

---

## 1. AgentBuilderAgent v1.0 必須要件
- schema_validate / proposal_validate の実行（validationMode="schema" 以上）
- existingTree/read_repo の取り込み
- 既存構造に寄せた skeleton 生成
- git_diff（仮想差分要約）を proposal に添付
- run_tests（sandbox）は validationMode="schema+tests" かつ ToolGate allow の場合のみ

---

## 2. ToolGate 連携（必須）
- Agent は Tool 実行前に ToolGate に evaluate を要求
- allow の場合のみ Tool を実行
- deny の場合：
  - proposal を継続し、summary に deny 理由を明記（提案止まりのまま）

参照：
- master__tool_gate_policy_v1__api_contract_v1_0.md

---

## 3. high-risk の扱い（v1.0）
- highRiskDetected=true でも提案は継続
- ただし high-risk path を changes.files に含めない
- manualSteps に human gate を必ず要求

---

# END