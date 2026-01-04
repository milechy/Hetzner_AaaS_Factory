# master__tool_gate_policy_v1__addendum_v1_1.md
AaaS Factory – ToolGate Policy Master (v1) Addendum (v1.1 GitHub Read)
最終更新: 2025-12-24

---

## 0. 目的
v1.1 で解禁する github_read（read-only）を ToolGate ポリシーとしてSSOT化する。

参照：
- master__tool_gate_policy_v1.md
- master__tool_gate_policy_v1__api_contract_v1_0.md

---

## 1. github_read のデフォルト方針
- effect=read
- humanApproved 不要
- riskLevel 不問（ただし出力に secret を含めない）
- blockedWhen.pathsPrefix は “write/changes” に対する制御が主目的のため、
  github_read 自体は deny しない（read-only で事実を収集する）

※ ただし Agent の提案（changes.files）側は、引き続き high-risk path を含めない。

---

## 2. 監査ログ
github_read の実行も監査対象：
- tool=github_read, effect=read, decision, reason, requestId/proposalId, policyVersion

---

# END