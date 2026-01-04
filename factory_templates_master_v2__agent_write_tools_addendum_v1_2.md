# factory_templates_master_v2__agent_write_tools_addendum_v1_2.md
AaaS Factory – Templates Master Addendum (Agent Limited Write Tools v1.2)
最終更新: 2025-12-24

---

## 0. 目的
Agent テンプレに v1.2（限定write: create_branch/create_pull_request）統合のための標準要件を追補する。

参照：
- master__tool_unlock_roadmap_v1__addendum_v1_2.md
- master__tool_gate_policy_v1__addendum_v1_2.md
- agent_specs_master_v2__write_tools_addendum_v1_2.md

---

## 1. テンプレ追加要件（必須）
- write tool 実行の前に ToolGate evaluate を必須化
- humanApproved は外部入力でのみ受け取る（Agentが生成しない）
- proposal.summary に必ず記載：
  - ToolGate decisions（allow/deny + reason）
  - 実行予定 tool と実行結果（success/failure）

---

## 2. 禁止事項（v1.2）
- merge/rebase/force-push
- PR comment/label 操作
- infra/apply/deploy
- secret 操作

---

## 3. 推奨：段階的ロールアウト
- 初期は humanApproved=true を付与した「限定運用」から開始
- maxFilesTouched を厳しめ（10）に固定し、段階的に見直す

---

# END