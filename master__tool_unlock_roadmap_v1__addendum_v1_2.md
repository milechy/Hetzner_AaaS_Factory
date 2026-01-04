# master__tool_unlock_roadmap_v1__addendum_v1_2.md
AaaS Factory – Tool Unlock Roadmap (v1) Addendum (v1.2 Limited Write)
最終更新: 2025-12-24

---

## 0. 目的
v1.2 において、write系ツール（create_branch / create_pull_request）の限定解禁をSSOT化する。
v1.1（github_read）を前提に、proposal-only を崩さず human gate による段階的解禁を行う。

参照：
- master__tool_unlock_roadmap_v1.md
- master__tool_unlock_roadmap_v1__addendum_v1_1.md
- master__tool_gate_policy_v1__api_contract_v1_0.md

---

## 1. v1.2 のスコープ
解禁（最小）：
- create_branch（effect=write）
- create_pull_request（effect=write）

非対象（v1.2では禁止）：
- merge / rebase / force-push
- PR comment / label 変更
- apply / deploy / infra 操作

---

## 2. v1.2 の運用フロー（human gate）
1) Agent が PullRequestProposal を生成（proposal-only）
2) Human Review（diff/影響範囲/安全性を確認）
3) Human が humanApproved=true を外部入力で付与（UI/CLI/API）
4) Agent を再実行（同一 proposalId を推奨）
5) ToolGate が allow の場合のみ、create_branch / create_pull_request を実行

---

## 3. v1.2 のガード条件（必須）
ToolGate allow の必須条件（AND）：
- humanApproved=true
- riskLevel=low
- highRiskDetected=false
- maxFilesTouched <= limit（推奨: 10）
- blockedWhen.pathsPrefix に抵触しない
- default-deny 維持（ルール未一致はdeny）

---

## 4. E2E シナリオ（v1.2）
- Scenario 6: humanApproved=true → PR作成成功
- Scenario 7: humanApproved=false → deny（no-call）
- Scenario 8: filesTouched > limit → deny
- Scenario 9: high-risk path 含有 → deny

---

# END