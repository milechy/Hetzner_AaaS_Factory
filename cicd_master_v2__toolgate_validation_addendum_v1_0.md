# cicd_master_v2__toolgate_validation_addendum_v1_0.md
CI/CD Master v2 Addendum – ToolGate Validation (v1.0)
最終更新: 2025-12-24

---

## 0. 目的
ToolGate Reference Implementation を継続的に安全運用するための最小 CI を標準化する。

---

## 1. 最小チェック（推奨）
Python:
- ruff (lint)
- pytest (test)

---

## 2. 推奨テスト観点
- blockedWhen.pathsPrefix に一致する pathsTouched → deny
- tool+effect の一致がない → default-deny
- allowedWhen 条件が満たされる → allow
- allowedWhen 条件が満たされない → deny

---

## 3. 禁止事項
- 本CIで apply/deploy を行わない
- secret をログ出力しない

---

# END