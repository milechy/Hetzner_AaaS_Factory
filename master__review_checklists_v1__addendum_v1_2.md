# master__review_checklists_v1__addendum_v1_2.md
AaaS Factory – Review Checklists Master Addendum (v1.2 Limited Write)
最終更新: 2025-12-24

---

## 0. 目的
v1.2（限定write）導入時の統合レビュー観点を追加する。
v1.1 の統合レビューに加え、「human gate」「write no-call」「監査」を明確化する。

参照：
- master__review_checklists_v1.md
- master__tool_gate_policy_v1__addendum_v1_2.md

---

## 1. v1.2 限定write 統合レビュー（追加）

### A. Safety（必須）
- [ ] v1.2で許可される write tool が create_branch/create_pull_request のみに限定されている
- [ ] merge/rebase/force-push が導入されていない
- [ ] infra/apply/deploy が導入されていない
- [ ] secrets/token/key がログおよび proposal content に含まれない

### B. Human Gate（必須）
- [ ] humanApproved は外部入力のみで与えられる（Agentが推測・自動付与しない）
- [ ] approval（approvedBy/approvedAt/comment）は監査用途であり、Agent判断に使っていない

### C. ToolGate（writeの厳格 gate）
- [ ] write 実行前に ToolGate evaluate(tool, effect=write) が必ず呼ばれる
- [ ] ToolGate deny の場合、write tool を実行しない（no-call）
- [ ] allow 条件が満たされないケースがテストで担保されている
  - [ ] humanApproved=false → deny
  - [ ] highRiskDetected=true → deny
  - [ ] filesTouched > limit → deny
  - [ ] blockedWhen.pathsPrefix 該当 → deny

### D. 監査（推奨）
- [ ] ToolGate audit に proposalId / tool / decision / reason / policyVersion が残る
- [ ] possible な場合、approvedBy/approvedAt も残る
- [ ] Agent summary に実行結果（success/failure）が短く記載される

---

# END