# agent_specs_master_v2__write_tools_addendum_v1_2.md
AaaS Factory – Agent Specs Addendum (v1.2 Limited Write Tools)
最終更新: 2025-12-24

---

## 0. 目的
Agent 実装における v1.2（限定write）の責務境界・入力拡張・失敗時挙動をSSOT化する。

参照：
- master__tool_unlock_roadmap_v1__addendum_v1_2.md
- master__tool_gate_policy_v1__addendum_v1_2.md

---

## 1. 原則（不変）
- Agent=判断、Tool=実行
- Tool 実行前に ToolGate evaluate 必須
- humanApproved は Agent が生成・推測してはならない（外部入力のみ）
- deny の場合は proposal-only にフォールバックして継続

---

## 2. 入力拡張（推奨：互換追加）
Request に以下を optional 追加してよい（v1.0/1.1破壊禁止）：
- humanApproved?: boolean（default false）
- approval?: { approvedBy?: string, approvedAt?: string(ISO), comment?: string }

注意：
- 判定条件は ToolGate の allowedWhen が主。Agent は approval を「監査/表示」目的に限定。

---

## 3. v1.2 実行ロジック（必須）
- create_branch / create_pull_request の実行前に：
  - ToolGate evaluate(tool, effect=write, context) を呼ぶ
  - allow の場合のみ実行
- context 必須項目：
  - humanApproved, riskLevel, highRiskDetected, pathsTouched, filesTouchedCount, domains
- 実行結果（success/failure）は proposal.summary に短く反映

---

## 4. 失敗時挙動（必須）
- ToolGate deny：ツール実行しない（no-call）＋ summary に deny 理由
- Tool 実行失敗：自動リトライしない（manualSteps に human action を追加）

---

# END