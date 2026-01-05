# Wiring Spec — Controlled Git v1.2
Hetzner × AaaS 自動開発ファクトリー（2025版）  
対象チャット: v1.2 実行有効化（wiring 設計）  
最終更新: 2026-01-04

---

## 0. 目的

`DisabledGitWriteTools` を **削除して危険に解禁する**のではなく、  
Human Approval と Policy によって制御された **ControlledGitTools** へ安全に差し替え、  
Factory を **「実行可能だが破壊しない」** 状態へ移行する。

本仕様は v1.2 における **実行パス（wiring）** の SSOT とする。

---

## 1. 不変条件（Invariant）

1. Agent は git write を直接実行しない（Agent/Tool 分離）
2. 変更は PR-only（直接反映しない）
3. High-risk（infra/security/billing/template/master）は自動実行しない
4. Human Approval が最終ゲート
5. Tool は deterministic（Policy SSOT に基づき同じ入力に同じ結論）

---

## 2. 正規シーケンス（強制順）

以下以外の順序は Tool 側で拒否してよい。

1. **Agent**: `PullRequestProposal`（JSON + patch）を生成
2. **Tool**: `policy_check(proposal, policy=controlled_git_policy_v1_2.json)`
3. **Human**: approve / reject → approve の場合のみ `ApprovalToken` 発行
4. **Tool**: `prepare_branch(repo, baseBranch, branchName, approval)`
5. **Tool**: `apply_proposal_patch(proposal, branchName, approval)` → commit 作成
6. **Tool**: `open_pull_request(repo, baseBranch, headBranch, title/body, approval)`
7. **CI**: GitHub Actions が PR 上で実行（通常フロー）
8. **Human**: review/merge（Factory は merge しない）

---

## 3. 停止点（v1.2 の “止まるべき場所”）

- `policy_check` が reject → 必ず停止（Approval を出しても進めない）
- Human が reject → 停止
- `apply_proposal_patch` が patch conflict → 停止（再提案・再生成へ）
- `open_pull_request` 失敗 → **原則停止**（人間判断でリトライ）
  - ただし **GitHub API 由来の 403（"Resource not accessible by personal access token" 等）** の場合は v1.2 では「停止」ではなく **フォールバック（PR 作成 URL を返す）** として扱い、Human が UI で PR を作成して前進できる。

---

## 4. 責務分解（Roles）

### 4.1 Agent（SelfDevAgent / 子エージェント）
**Do**
- SSOT 参照に基づく計画
- `PullRequestProposal` の生成
- （任意）self-reported risk を proposal に付与（参考値）

**Do Not**
- git 操作（branch/commit/push/PR作成）
- secrets 操作
- high-risk の “実行”

### 4.2 Tool（ControlledGitTools）
**Do**
- `policy_check` による最終判定（risk 再計算・上書き）
- ApprovalToken 検証（hash binding / 失効）
- branch / commit / PR 作成
- 監査ログ（JSONL append-only）

**Do Not**
- merge
- deploy
- policy ファイルの自己改変

### 4.3 Human
- Approval（approve/reject）
- PR review / merge の最終判断

---

## 5. Tool Registry（有効化 / 無効化）

### 5.1 v1.2 で有効化する Tool セット
- Read-only / Proposal: `read`, `search`, `git_diff`, `ci_check`, `pr_proposal`（または proposal generator）
- Controlled Git: `policy_check`, `prepare_branch`, `apply_proposal_patch`, `open_pull_request`

### 5.2 v1.2 で無効化（または非公開）にする Tool
- `DisabledGitWriteTools` をデフォルト toolset から除外（互換モードのみ）
- 直接 git write 系（存在する場合）も同様に除外

---

## 6. DisabledGitWriteTools → ControlledGitTools 置換

### 6.1 置換マッピング
| 旧（無効化） | 新（v1.2） |
|---|---|
| write/apply changes | proposal 生成（JSON/diff） |
| commit/push | `apply_proposal_patch`（Approval 必須） |
| open PR | `open_pull_request`（Approval 必須） |

### 6.2 Feature Flag（後方互換）
`GIT_WRITE_MODE = "disabled" | "controlled_v1_2"`

- default: `"controlled_v1_2"`
- `"disabled"`: 旧挙動（常に no-op / 拒否）

---

## 7. Policy SSOT（参照の固定）

`policy_check` は必ず以下を参照する：

- `config/policy/controlled_git_policy_v1_2.json`

ルール：
- proposal 内 `risk` は参考値（Tool が再計算）
- High-risk を含む場合は token があっても reject（v1.2）

---

## 8. Human Approval（確定仕様）

### 8.1 Approval 入口
v1.2 は CLI を正とする（UI は後回し可）。

例：
- `cg approve --request approval_request.json --actor <id> > approval_token.json`

### 8.2 ApprovalToken の要件
- `proposalHash` に強くバインド
- `expiresAt` 必須（短期）
- `actions` は v1.2 では固定セットでよい（prepare/apply/open）

---

## 8.3 GitHub 認証（v1.2 の現実解）

v1.2 は **完全自動 PR 作成**を要件にしない（安全性優先）。
GitHub 認証は環境差・権限制約により API が 403 になることがあるため、次の優先順位とする。

1) **GitHub App（推奨）**
   - Contents: Read/Write
   - Pull requests: Read/Write
   - Metadata: Read
   - 監査・ローテーションが容易で、PAT のコピー事故を回避できる。

2) **PAT / Deploy key 等（フォールバック）**
   - git push が可能であれば `prepare_branch/apply_proposal_patch` は成立する。
   - PR 作成 API が通らない場合は `open_pull_request` は **PR 作成 URL** を返し、Human が UI で作成する。

---

## 9. 監査ログ（最小）

ControlledGitTools は JSONL（append-only）で記録：

- `POLICY_CHECKED`（decision, matched rules）
- `APPROVAL_VERIFIED`（token id, actor）
- `BRANCH_PREPARED`（branch, sha）
- `PATCH_APPLIED`（commit, appliedFiles, skippedFiles）
- `PR_OPENED`（pr number/url）
- `PR_OPEN_FALLBACK`（prCreateUrl, reason/status/message）

## 9.1 open_pull_request のフォールバック仕様（v1.2）

GitHub API による PR 作成が失敗する場合でも、v1.2 は **前進可能**であることを重視する。

- 成功時: `PR_OPENED` を記録し、`prUrl` を返す。
- 失敗時:
  - HTTP 403 かつメッセージが `Resource not accessible by personal access token` 等の場合は、
    Tool は **停止ではなくフォールバック**として次を返す：
    - `prCreateUrl = https://github.com/{repo}/pull/new/{headBranch}?expand=1`
    - 監査ログに `PR_OPEN_FALLBACK`（reason, status, message）を追記
  - それ以外の失敗（422/409/ネットワーク等）は **停止**として扱い、Human 判断でリトライ。

注: v1.2 は merge を行わず、PR 作成後の review/merge は Human に限定する。

---

## 10. 強制ガード（実装要件）

- **順序ガード**：`apply_proposal_patch` / `open_pull_request` は、直前の `policy_check` と token hash binding が一致しないと拒否
- **再計算ガード**：policy は毎回ロード（または起動時ロード＋ハッシュ監視）
- **部分適用禁止（v1.2）**：`reject_if_any_reject` を尊重
- **high-risk は token があっても拒否**：Human Gate は “許可の前提” に過ぎない

---

# END
