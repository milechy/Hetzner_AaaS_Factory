# master__tool_unlock_roadmap_v1.md
AaaS Factory – Tool Unlock Roadmap (v1)
最終更新: 2025-12-24

---

## 0. 目的
Agent プロジェクトを v0（proposal-only）から v1（限定 Tool 解禁）へ安全に進化させるための
**段階的解禁ロードマップ**をSSOTとして定義する。

前提：
- Agent = 判断（計画・提案）
- Tool = 実行（副作用あり）
- high-risk（infra / security / billing / template）は段階的に解放し、原則 Human Gate を要求する。

---

## 1. バージョン段階

### v0（現在）
- 出力：PullRequestProposal(JSON) で停止
- 禁止：git write / PR 作成 / merge / infra / secret 操作
- LLM：LLMRouter 経由（profile-only）

### v1.0（Safe Tools 解禁）
目的：提案の精度・再現性を上げる（副作用なし）
解禁 Tool（read/validate系）：
- read_repo（読み取り）
- schema_validate（JSON Schema検証）
- proposal_validate（提案妥当性検証）
- git_diff（差分生成：ローカル/仮想）
- ci_check（読み取り・検証のみ）
- run_tests（サンドボックス/読み取り：結果取得のみ）

禁止：
- git commit / push / PR create / merge
- high-risk の実行・変更適用

### v1.1（Observability / Read-only 拡張）
目的：既存変更・CI状況を取り込み、競合と失敗を減らす
解禁 Tool（read-only API）：
- github_read（PR/Issue/CI status の取得）
- artifact_read（ログ/成果物の読み取り）

禁止：
- PR create / merge はまだ不可

### v1.2（Limited Write with Human Gate）
目的：人間承認のもとで PR 作成までを自動化
条件付き解禁 Tool（副作用あり）：
- create_branch
- create_pull_request

必須条件（すべて満たす）：
- Human Approval = true
- risk.highRiskDetected = false（または対象ドメインが明示的に許可）
- Branch Protection 有効
- CODEOWNERS 有効
- PR テンプレート / チェック必須（最低 lint/test）

禁止：
- merge の自動化
- high-risk ドメイン（infra/security/billing/template）への変更適用（別の段階で解放）

---

## 2. high-risk の扱い（段階解放）
- v0/v1.0/v1.1：検出のみ（ファイル生成/適用を禁止）
- v1.2：原則禁止（例外は “明示許可 + human gate” のみ）
- v2以降：ドメイン別に解放（security は常に human gate を要求）

---

## 3. 原則：Agent は Tool 解禁判断をしない
- 解禁判断は **ToolGate Policy（SSOT）** が行う
- Agent は「Toolを使いたい」提案と根拠を出すのみ

参照：
- master__tool_gate_policy_v1.md

---

# END