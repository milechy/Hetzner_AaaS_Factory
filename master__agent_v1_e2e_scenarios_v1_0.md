# master__agent_v1_e2e_scenarios_v1_0.md
AaaS Factory – Agent v1.0 E2E Scenarios (SSOT)
最終更新: 2025-12-24

---

## 0. 目的
Agent v1.0（Safe Tools 解禁）の運用を再現可能にするため、
代表 E2E シナリオをSSOT化する。

---

## 1. シナリオ1：low-risk / existingTreeあり / schema+tests
- Input: validationMode="schema+tests", existingTree あり
- Steps:
  1) schema_validate(request) OK
  2) risk_detect: low
  3) ToolGate allow: read_repo/git_diff/run_tests/ci_check
  4) 既存構造に寄せて skeleton（modify優先）
  5) git_diff 要約を summary に添付
  6) run_tests 結果を summary に添付
  7) proposal_validate OK
  8) PullRequestProposal を返す

Expected:
- changes.files は modify 優先
- validation.checks に lint/test
- summary に diff要約 + test結果

---

## 2. シナリオ2：high-risk検出 / 提案継続（ファイル除外）
- Input: specに billing/infra 等のシグナル
- Steps:
  1) risk_detect: highRiskDetected=true
  2) ToolGate allow（read/validateのみ）
  3) skeleton は生成するが high-risk path を changes.files から除外
  4) summary に除外理由を明記
  5) manualSteps に human gate を要求
  6) PullRequestProposal を返す

Expected:
- risk.level=high
- files に high-risk prefix が含まれない
- manualSteps に human gate

---

## 3. シナリオ3：ToolGate deny（write要求）
- Input: 誤って write tool（create_pull_request 等）を要求
- Steps:
  1) ToolGate deny（v1.0ではwrite禁止）
  2) Agent は proposal を継続し、summary に deny 理由を明記
  3) PullRequestProposal を返す（proposal-only維持）

Expected:
- 実行は行われない
- deny理由が追跡可能

---

# END