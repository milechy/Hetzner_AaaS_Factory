# Security Checklist v2

## 0. 強制ルール

以下は必須：

- Branch Protection
- CODEOWNERS
- PR-only change
- Agent write 権限禁止

---

## 1. Agent SDK 対応

- Tool permission が security boundary
- high-risk tool は human gate 必須
# master__security_checklist_v3.md

## Security Checklist v3

最終更新: 2025-12-01

---

## 0. 強制ルール

以下は必須：

- Branch Protection
- CODEOWNERS
- PR-only change
- Agent write 権限禁止

---

## 1. Agent SDK 対応

- Tool permission が security boundary
- high-risk tool は human gate 必須

---

## 2. High-Risk Tool 定義

high-risk tool とは以下を指す：

- deploy/production 変更権限
- secrets 取得・変更権限
- admin API 呼び出し
- mobile_device_control（MCP等を含む）

これらは必ず human gate (人間による承認) を通す。

---

## 3. mobile-mcp 統制要件

### 3.1 実行制限
- MCP (Mobile Control Platform) への操作は Agent 経由のみ許可
- 手動端末操作や未承認 device 登録は禁止
- E2E workflow の実行権限は CODEOWNERS で制限

### 3.2 データ保護
- テスト証明書/Secrets は MCP vault 管理
- テストデータ/ログ/スクリーンショットは artifact 扱いし、公開範囲を限定

### 3.3 監査
- すべての MCP 操作は audit log に記録
- device install/uninstall, 証明書更新などは必ず記録されること

---

## 4. その他

- Agent 以外の workflow 編集禁止
- .env ファイルの禁止
- main 直接 push の禁止

---