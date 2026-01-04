# master__review_checklists_v1.md
AaaS Factory – Review Checklists Master (v1)
最終更新: 2025-12-24

---

## 0. 目的
proposal-only / tool-gated な Agent 開発運用における「人間レビュー」の標準チェック項目をSSOT化する。

対象：
- AgentBuilderAgent v1.0+
- ToolGate v1.0+
- 付随する PullRequestProposal(JSON) 成果物

---

## 1. AgentBuilderAgent v1.0 Proposal レビューチェックリスト

### A. 契約・出力
- [ ] 出力が PullRequestProposal(JSON) または AgentBuilderError(JSON) のみ
- [ ] changes.files に high-risk prefix が含まれていない
  - infra/, ops/, .github/, templates/, security/, billing/
- [ ] risk.highRiskDetected=true の場合：
  - [ ] validation.manualSteps に human gate が含まれる
  - [ ] summary に「高リスク検出によりファイル除外」が明記されている

### B. v1.0 追加要件（Safe Tools）
- [ ] summary に ToolGate decisions（allow/deny + reason）が記載されている
- [ ] validationMode の説明がある（none/schema/schema+tests）
- [ ] existingTree が与えられている場合：
  - [ ] modify 優先（新規乱立を避ける）
  - [ ] 既存構造（src/tests/既存パッケージ）に沿う

### C. 安全性
- [ ] write 系の意図（create_branch/create_pull_request/merge/apply/deploy）が含まれない
- [ ] secrets/token/key を含む content がない
- [ ] 実行コマンドは validation.checks に列挙され、結果は summary に短文（スキーマ維持）

---

## 2. ToolGate（Policy Engine）レビューチェックリスト

### A. 契約・評価順
- [ ] POST /v1/evaluate を実装
- [ ] 評価順が blockedWhen → allowedWhen → default-deny
- [ ] ルール未一致は deny（default-deny）

### B. high-risk ブロック
- [ ] blockedWhen.pathsPrefix が SSOT 準拠
- [ ] pathsTouched に high-risk が含まれる場合 deny される

### C. 監査ログ
- [ ] ts, requestId, proposalId, tool, effect, decision, reason, policyVersion を記録

### D. 認証
- [ ] TOOLGATE_API_KEY 設定時のみ Bearer 必須（任意運用）

---

## 3. v1.1 提案セット（GitHub read-only 統合）統合レビュー項目（追補）

### 3.1 対象（v1.1セットの典型構成）
推奨の採用順（実装 → policy → tests → testability）：
1) AgentBuilderAgent v1.1 最小パッチ（GitHub read-only + ToolGate gated）
2) ToolGate policy（テンプレ）v1.1：github_read(effect=read) 明示許可（default-deny維持）
3) v1.1 テスト：Scenario 4/5（overlap PR / CI failure）
4) v1.1 統合寄せテスト：build_proposal の summary/manualSteps 伝播
5)（任意）DI最小パッチ：monkeypatch排除（AgentDeps等）

※ proposal-id / ファイル名はプロジェクトの proposals/ 配下で管理する。

### 3.2 合否の要点（必須）
#### A. Safety（proposal-only 維持）
- [ ] GitHub write（PR作成・コメント・ラベル変更・merge）が導入されていない
- [ ] git write / apply / deploy / infra 操作が導入されていない
- [ ] token/secret がログおよび proposal content に含まれない

#### B. ToolGate（github_read の厳格 gate）
- [ ] github_read の前に ToolGate evaluate が必ず呼ばれる（tool=github_read, effect=read）
- [ ] deny の場合、GitHub client を呼ばない（no-call）
- [ ] ToolGate decision（allow/deny + reason）が proposal.summary に必ず残る
  - 例：ToolGate decisions: - github_read:allow:...

#### C. GitHub Facts の反映（提案品質）
- [ ] summary に “GitHub Facts” セクションが追加される（requested時）
- [ ] 重複PR兆候がある場合：
  - [ ] summary に warning 相当の記載（PR識別子/URL等の短文）
  - [ ] validation.manualSteps に「重複整理方針確認」等の human action が追加される
- [ ] CI failure（metadata+ci）がある場合：
  - [ ] summary に失敗ジョブの短文（name/conclusion/status）
  - [ ] validation.manualSteps に「失敗の再現/確認」等の human action が追加される

### 3.3 テスト（必須）
- [ ] network を使わない（stub / DI / monkeypatch 等で GitHub/Router を遮断）
- [ ] 少なくとも以下の3ケースがカバーされている
  - [ ] Scenario 4：overlap PR → facts + manualSteps
  - [ ] Scenario 5：CI failure（metadata+ci）→ facts + manualSteps
  - [ ] ToolGate deny → no-call（GitHub API が呼ばれない）

### 3.4 ロールアウト（推奨）
- [ ] 初期は githubReadMode=metadata（default）で運用
- [ ] metadata+ci は必要な場合のみ（GITHUB_TOKEN は read-only / fine-grained 推奨）

---

## 4. v1.2 提案セット（限定 write: create_branch/create_pull_request）統合レビュー項目（追補）

参照SSOT：
- master__tool_unlock_roadmap_v1__addendum_v1_2.md
- master__tool_gate_policy_v1__addendum_v1_2.md
- agent_specs_master_v2__write_tools_addendum_v1_2.md
- factory_templates_master_v2__agent_write_tools_addendum_v1_2.md
- master__review_checklists_v1__addendum_v1_2.md

### 4.1 対象（v1.2セットの典型構成）
推奨の採用順（policy → agent → tests）：
1) ToolGate policy（テンプレ）v1.2：create_branch/create_pull_request の write 条件追加
2) AgentBuilderAgent v1.2：humanApproved 入力 + ToolGate-gated write 実行（deny→no-call）
3) v1.2 テスト：Scenario 6〜9（human gate / limit / high-risk / blockedWhen）

推奨 proposal（例）：
- ToolGate template v1.2 policy proposal：
  - prp_toolgate_template_v12_policy_20251224.json
- AgentBuilderAgent v1.2 min patch proposal：
  - prp_agent_builder_v12_minpatch_write_tools_20251224.json

### 4.2 合否の要点（必須）
#### A. Safety（v1.2の禁止事項が守られている）
- [ ] v1.2 で導入される write tool は create_branch/create_pull_request のみ
- [ ] merge/rebase/force-push が導入されていない
- [ ] PR comment/label 変更が導入されていない
- [ ] apply/deploy/infra 操作が導入されていない
- [ ] token/secret がログおよび proposal content に含まれない

#### B. Human Gate（外部入力のみ）
- [ ] humanApproved は外部入力のみ（Agent が推測・自動付与しない）
- [ ] approval（approvedBy/approvedAt/comment）は監査/表示目的のみ（判定条件に使わない）

#### C. ToolGate（writeの厳格 gate）
- [ ] write 実行前に ToolGate evaluate(tool, effect=write) が必ず呼ばれる
- [ ] deny の場合、write tool を実行しない（no-call）
- [ ] allow 条件（AND）がポリシーで満たされている：
  - [ ] humanApproved=true
  - [ ] riskLevel=low
  - [ ] highRiskDetected=false
  - [ ] filesTouchedCount <= maxFilesTouched（推奨:10）
  - [ ] blockedWhen.pathsPrefix に抵触しない
- [ ] ToolGate decision（allow/deny + reason）が proposal.summary に必ず残る
- [ ] 実行結果（success/failure）が proposal.summary に短く反映される（runtime時）

### 4.3 テスト（必須：Scenario 6〜9）
- [ ] network を使わない（stub/DIで遮断）
- [ ] 少なくとも以下の4ケースがカバーされている
  - [ ] Scenario 6：humanApproved=true + low + safe → allow（tool call attempted）
  - [ ] Scenario 7：humanApproved=false → deny（no-call）
  - [ ] Scenario 8：filesTouchedCount > limit → deny（no-call）
  - [ ] Scenario 9：high-risk path / highRiskDetected=true → deny（no-call）

### 4.4 ロールアウト（推奨）
- [ ] 初期は「Human Review → humanApproved=true 付与 → 再実行」の限定運用
- [ ] maxFilesTouched は厳しめ（10）固定から開始し、段階的に見直す

---

# END