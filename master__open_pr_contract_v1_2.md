# master__open_pr_contract_v1_2.md
================================================
AaaS Factory – Open PR Contract (v1.2)
SSOT: Single Source of Truth
================================================

## 📘 概要（Purpose）

本ドキュメントは、AaaS Factory における  
**Pull Request 作成（Open PR）を自動化・半自動化するための最小かつ厳格な契約（Contract）** を定義する。

本 Contract は **SSOT（Single Source of Truth）** として扱われ、以下すべてが必ず従う。

- Agent（AgentBuilderAgent v1.2 以降）
- CLI（controlled_git.cli）
- ToolGate
- Human Approval（外部承認者）
- GitHub API 呼び出し

---

## 🎯 v1.2 Contract の目的

- PR 作成を **「提案」から「条件付き実行」へ昇格**
- 人間の明示的承認を **必須ゲート** として組み込む
- 誤操作・権限逸脱・サプライチェーン事故を防止
- GitHub API の 401 / 403 を **安全に扱い、必ずフォールバック可能** にする

---

## 📌 対象スコープ（In Scope）

本 Contract は以下の write 操作を対象とする。

- `create_branch`
- `create_pull_request`
- GitHub API を用いた Open PR
- CLI / Agent による自動実行

以下は **明示的に対象外**。

- merge / squash / rebase
- deploy / infra 反映
- secrets / billing / security 操作

---

## ✅ 1. Hard Requirements（必須条件）

以下は **すべて満たされなければならない**。

1. `humanApproved == true`
2. 有効な Approval Token（HMAC 署名・期限内）
3. Approval Token の `actorId` が CLI 実行主体と一致（v1.2 では強い必須条件：不一致/欠落は 403 相当で deny）
4. ToolGate による write tool の `allow`
5. high-risk path を含まないこと

いずれか一つでも不成立の場合：

> **write 系ツールは一切実行してはならない**

---

## 🔐 2. Approval Token（v1.2）

Approval Token は以下の性質を持つ。

- HMAC 署名付き JSON
- 明示的な有効期限（`expiresAt`）
- スコープ制限：
  - `repo`
  - `baseBranch`
  - `actions`
- **actorId を必須で含む**

### actorId について

- **v1.2 では強い必須条件（mandatory-by-default）**
- CLI 実行者（--actor / CG_ACTOR / GITHUB_ACTOR）と Token scope の一致確認に使用
- `actorId` 欠落または不一致は **deny(403 相当)** として扱い、write 実行は一切しない

---

## 🧠 3. ToolGate の役割

ToolGate は **最終的な実行可否判定者** である。

評価項目：

- `humanApproved`
- `riskLevel`
- `highRiskDetected`
- `pathsTouched`
- `filesTouchedCount`
- `domains`

### write tool 実行条件

- ToolGate が `allow` を返した場合のみ実行可能
- `deny` の場合、理由を summary に記録し **即停止**

---

## 🌐 4. GitHub API 実行ルール

### Base URL

- GitHub API Base URL は **推奨（SHOULD）設定項目**（org/enterprise や GitHub Enterprise Server を想定）
- default: `https://api.github.com`

### 認証

- Fine-grained PAT または PAT（write 権限必須）

### 401 / 403 の扱い（重要）

- 401 / 403 で **例外停止しない（Fail Safe）**
- API 失敗時は **必ずフォールバック URL を返す**
  - 401: token 不正/期限切れ/貼り付けミスなど（理由コードは `gh_401`）
  - 403: 権限不足/Org policy/Fine-grained 制限など（理由コードは `pat_403` 等の *best-effort* 分類。分類は推奨であり、fallback の成立条件ではない）

フォールバック URL：

https://github.com/{owner}/{repo}/pull/new/{head}?expand=1

---

## 🛟 5. フォールバック原則（Fail Safe）

自動 Open PR が失敗しても、以下を保証する。

- PR 作成用 URL を常に生成
- Proposal（JSON）は破棄しない
- 人間がブラウザで安全に引き継げる状態を維持

---

## 🚫 6. 明示的禁止事項（Forbidden）

以下は **絶対禁止**。

- `humanApproved=false` での PR 作成
- Approval Token の期限切れ使用
- actorId 不一致での実行
- ToolGate 未評価での write 実行
- merge / deploy の自動実行

---

## 📎 7. 実装準拠対象

本 Contract に準拠すべき実装：

- `controlled_git.cli approve / open-pr`
- `AgentBuilderAgent v1.2`
- ToolGate policy `toolgate_v1`
- CI / Security Review

---

## 🏁 終わりに

本 Contract は **拡張可能だが後方互換を維持する**。

- v1.3 以降は必ず本 Contract を基準に差分追加する
- 本ファイルは README / Docs / Agent 実装より **常に優先される**

---

END