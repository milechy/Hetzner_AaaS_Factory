## `cicd_master_v2__proposal_validation_addendum.md`
（proposal-only の標準CIだけを抜粋してSSOT化）

```md
# CI/CD Master v2 Addendum – Proposal Validation (Agent Projects)
最終更新: 2025-12-24

---

## 0. 目的
proposal-only な Agent プロジェクト（v0）向けに、最小 CI を標準化する。
- PR作成/merge/デプロイは禁止（提案のみ）

---

## 1. 最小チェック
Python:
- ruff (lint)
- pytest (test)

推奨：
- 依存解決は lock 管理（ただし v0 は lock 更新も提案のみ）

---

## 2. 禁止事項
- apply/merge/deploy を CI で実行しない
- secret をログに出さない

---

# END