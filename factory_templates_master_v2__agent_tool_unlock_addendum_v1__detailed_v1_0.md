# factory_templates_master_v2__agent_tool_unlock_addendum_v1__detailed_v1_0.md
AaaS Factory – Templates Master Addendum (Agent Tool Unlock v1) Detailed (v1.0)
最終更新: 2025-12-24

---

## 0. 目的
factory_templates_master_v2__agent_tool_unlock_addendum_v1.md を補完し、
v1.0で必要となる “テンプレの追加構造” をSSOT化する。

---

## 1. v1.0 テンプレ追加（推奨）
Agent プロジェクトは以下を持つこと：
- toolgate_client（ToolGate evaluate）
- validators（schema/proposal validate）
- repo_reader（existingTree/read_repo ingest）
- diff_planner（既存寄せ + 仮想diff生成）

---

## 2. 提案出力の運用（スキーマ維持）
- diff 要約・検証結果は proposal.summary に記載
- validation.checks は “実行したコマンド” を列挙（結果は summary）

---

# END