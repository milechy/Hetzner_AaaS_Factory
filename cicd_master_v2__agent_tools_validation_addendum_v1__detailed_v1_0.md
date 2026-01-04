# cicd_master_v2__agent_tools_validation_addendum_v1__detailed_v1_0.md
CI/CD Master v2 Addendum – Agent Tools Validation Detailed (v1.0)
最終更新: 2025-12-24

---

## 0. 目的
cicd_master_v2__agent_tools_validation_addendum_v1.md を補完し、
v1.0の “検証系 Tool” と CI の整合をSSOT化する。

---

## 1. v1.0 推奨チェック
- schema_validate（request/proposal）
- lint（ruff）
- test（pytest）
- proposal_validate（構造・policy整合）

---

## 2. v1.0 禁止
- apply / merge / deploy を CI で実行しない
- secret をログ出力しない

---

# END