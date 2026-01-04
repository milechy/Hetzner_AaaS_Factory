# factory_templates_master_v2__agent_tool_unlock_addendum_v1.md
AaaS Factory – Templates Master Addendum (Agent Tool Unlock v1)
最終更新: 2025-12-24

---

## 0. 目的
Factory Templates v2 に対して、Agent プロジェクトの v1（限定 Tool 解禁）を追補する。

---

## 1. 適用対象
- apps/agents 配下の Agent Projects
- v0（proposal-only）から v1（safe tools / read-only / limited write）へ進化させる全テンプレ

---

## 2. 参照SSOT
- master__tool_unlock_roadmap_v1.md
- master__tool_gate_policy_v1.md

---

## 3. テンプレ要件（v1）
### v1.0
- repoContext.existingTree を利用して差分寄せを行える構成
- schema_validate / proposal_validate を組み込める構成
- run_tests / ci_check を “sandbox/validate” として実行できる構成

### v1.1
- github_read の導入余地（read-only）
- CI status を提案内容に反映できる構成

### v1.2
- create_pull_request は human gate を前提にした “別フロー” として分離
- merge は v1 では禁止

---

# END