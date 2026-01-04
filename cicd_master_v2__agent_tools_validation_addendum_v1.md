# cicd_master_v2__agent_tools_validation_addendum_v1.md
CI/CD Master v2 Addendum – Agent Tools Validation (v1)
最終更新: 2025-12-24

---

## 0. 目的
Agent v1（Tool 解禁）に合わせて、proposal の妥当性と安全性を CI 観点で担保する。

---

## 1. v1.0 最小チェック（推奨）
- schema_validate（入力/出力 JSON Schema）
- lint（ruff 等）
- test（pytest）
- proposal_validate（構造・ポリシー整合）

---

## 2. v1.2 条件付きチェック（PR作成前提）
- humanApproved=true が必要（CI 自体ではなく手続き要件）
- Branch Protection / CODEOWNERS の存在確認（チェック項目化推奨）
- 高リスクパス（infra/, ops/, .github/, templates/, security/, billing/）を含む変更を検知したら fail

---

## 3. 禁止事項
- apply/merge/deploy を CI で実行しない（v1は提案/PR作成まで）
- secret をログ出力しない

---

# END