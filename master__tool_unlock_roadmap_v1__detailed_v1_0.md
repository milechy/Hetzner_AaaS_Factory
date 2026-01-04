# master__tool_unlock_roadmap_v1__detailed_v1_0.md
AaaS Factory – Tool Unlock Roadmap (v1) Detailed (v1.0)
最終更新: 2025-12-24

---

## 0. 目的
master__tool_unlock_roadmap_v1.md を補完し、v1.0（Safe Tools 解禁）における
**実装準備に必要な追加仕様**をSSOTとして定義する。

---

## 1. v1.0 の追加仕様（Request 拡張：後方互換）
v0 schema を破壊しない（optional追加）前提で、運用上の推奨を定義する。

### 1.1 AgentBuilderRequest 推奨追加フィールド
- toolPolicyVersion?: string（例: "toolgate_v1"）
- validationMode?: "none" | "schema" | "schema+tests"（default: "schema"）
- repoContext.existingTree: v1.0 では “運用上必須” を推奨（schema上は任意でも可）

### 1.2 validationMode の意味
- none: 検証を実行しない（v0互換）
- schema: 入出力の schema_validate / proposal_validate を必須
- schema+tests: schema に加えて run_tests（sandbox）を実行し、結果を提案に添付

---

## 2. v1.0 実行フロー（標準）
1) schema_validate(request)
2) parse_spec + normalize（name/purpose必須、stepsは推論可）
3) repo ingest（existingTree または read_repo）
4) risk_detect（high-risk 判定）
5) ToolGate decision（allow/deny）
6) plan_targets（既存構造に寄せる）
7) generate_skeleton（high-risk file omit）
8) git_diff（仮想差分）→ summary に差分要約を追加
9) optional run_tests（validationMode="schema+tests" かつ ToolGate allow の場合）
10) proposal_validate(proposal)
11) PullRequestProposal(JSON) を返す（提案で停止）

---

## 3. v1.0 “差分精度” ルール（必須）
- 既存に似せる：existingTree がある場合、配置/命名を踏襲する
- modify優先：既存ファイルがあるなら modify を優先する（新規乱立禁止）
- diff要約：仮想diffを proposal.summary か manualSteps に必ず含める
- 検証結果：lint/test の結果は summary に短く記載（スキーマ拡張はしない）

---

## 4. high-risk の扱い（v1.0）
- highRiskDetected=true の場合でも提案は継続してよい
- ただし以下を必須：
  - changes.files から high-risk path を除外
  - summary に “除外した理由” を明記
  - manualSteps に human gate を要求

---

# END