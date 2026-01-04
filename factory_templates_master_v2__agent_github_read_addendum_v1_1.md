# factory_templates_master_v2__agent_github_read_addendum_v1_1.md
AaaS Factory – Templates Master Addendum (Agent GitHub Read v1.1)
最終更新: 2025-12-24

---

## 0. 目的
Agent テンプレに GitHub read-only（v1.1）統合のための標準要件を追補する。

---

## 1. テンプレ追加要件（推奨）
- github_read client（read-only）
- github facts formatter（summary に短く整形）
- ToolGate evaluate 呼び出し（github_read 前に必須）

---

## 2. 反映先（運用）
- Proposal.summary に GitHub Facts を追加（スキーマ維持）
- 既存PR重複やCI失敗がある場合は summary/manualSteps に明記

---

# END