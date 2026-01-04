# agent_specs_master_v2.md
AaaS Factory – Agent Specifications Master (v2)
最終更新: 2025-12-24

---

# 🎯 目的（Purpose）
本ドキュメントは Hetzner × AaaS Factory 全体を構成する
**全エージェントの仕様・API・責務範囲・階層構造を統一的に定義した唯一のマスター（SSOT）** である。

v2 では、Agent/Tool 分離、PR-only、LLMRouter 強制、モデルプール参照、high-risk 分離を正式採用する。

---

# 🔒 0. Global Safety & Execution Rules（v2 追加）

## 0.1 Agent / Tool 分離
- Agent = 判断・計画
- Tool = 実行
- Agent が直接行うことは禁止：
  - git write / push / merge
  - infra change
  - secret 操作

## 0.2 PR-only / Human Approval
- 変更は PR 提案（proposal）として表現すること。
- Human Approval 前に実環境・本番・秘密情報へ影響する実行を禁止する。

## 0.3 LLM Routing（モデル非依存）
- Agent は LLM を直接選ばない（model ID の直指定禁止）
- **必ず LLMRouter を経由**
- Agent が指定できるのは profile のみ

## 0.4 High-risk ドメイン（v2）
high-risk ドメイン：
- infra / security / billing / template

原則：
- low-cost model に割り当てることを禁止（Router 側の責務）
- v0 実装では high-risk のファイル生成を行わない（提案は限定）

---

# 🧠 1. Agent Architecture（階層構造）

             ┌────────────────────┐
             │   Manager Agent    │
             └──────────┬─────────┘
                        │ calls
    ┌───────────────────┼──────────────────────┐
    │                   │                      │
┌───────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ ArchitectAgent │  │ UIDesignAgent   │  │ API/DBDesignAgent│
└──────┬──────────┘  └───────────┬──────┘  └──────────┬───────┘
│                         │                     │
┌──────┴──────────┐    ┌─────────┴─────────┐    ┌─────┴────────┐
│ WebDevAgent      │    │ SwiftDevAgent     │    │ BackendAgent  │
└──────┬───────────┘    └──────────┬────────┘    └───────────────┘
│                            │
┌──────┴────────────┐   ┌──────────┴────────┐
│ CICDAgent          │   │ RepoBuilderAgent  │
└─────────┬──────────┘   └──────────┬────────┘
│                         │
┌┴────────────────┐   ┌─────┴──────────┐
│ TemplateAgent     │   │ AutomationAgent│
└──────────────────┘   └────────────────┘

L1: Manager
L2: Design & Planning
L3: Implementation（含: AgentBuilderAgent）

---

# 🧩 2. AgentBuilderAgent v0（Implementation Layer）

## 2.1 目的
AgentBuilderAgent v0 は、Spec（YAML/JSON）から
- skeleton（ディレクトリ/ファイル草案）
- PullRequestProposal(JSON)
を生成し、**提案で停止**する（git/PR作成/mergeは行わない）。

## 2.2 スコープ（v0）
### Do
- Spec parse（YAML/JSON）
- Skeleton（ファイルツリー＋内容草案）生成
- PR 提案（PullRequestProposal v0）生成

### Do Not
- git write / push / merge / GitHub PR 作成
- infra change / secret 操作
- high-risk ドメイン（infra/security/billing/template）のファイル生成

## 2.3 入力（AgentBuilderRequest v0）
- 形式：JSON
- 必須キー（合意事項）：
  - spec 内：`name`, `purpose` のみ必須（steps は推論補完）
- Schema SSOT：
  - `schemas__agent_builder_request_v0.json`

## 2.4 出力（PullRequestProposal v0）
- 形式：JSON（厳密スキーマ）
- Schema SSOT：
  - `schemas__pull_request_proposal_v0.json`

## 2.5 エラー（AgentBuilderError v0）
- 失敗時も JSON（構造化）
- Schema SSOT：
  - `schemas__agent_builder_error_v0.json`

## 2.6 High-risk 検出時の挙動（合意事項）
- Skeleton は生成して良い
- ただし high-risk ドメインに該当するファイルは `changes.files` に含めない
- `risk.highRiskDetected=true` を必ず立て、`risk.notes` に根拠を列挙する
- `validation.manualSteps` に human gate を要求する

## 2.7 LLM Routing（v0）
- Agent は `routingProfile` のみ指定可能
- すべて LLMRouter を経由（model ID 直指定禁止）
- `metadata.routerProfile` に採用 profile を記録

---

# 🧪 3. Tools（標準）
- read
- test
- git_diff
- pr_proposal
- ci_check

※すべて Tool 経由。Agent の直接実行は禁止。

---

# END