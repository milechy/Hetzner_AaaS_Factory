# api_standards_master_v1.md
AaaS Factory – API Standards Master (v1)  
最終更新: 2025-11-14

---

# 🎯 Purpose（目的）

本ファイルは AaaS Factory における  
**すべての API 設計・命名・バージョニング・認証・レスポンス形式の標準** を定める  
“API の唯一の真理（SSOT）” である。

対象：

- SaaSごとの Backend API（FastAPI / Node など）
- iOS / Web クライアントが叩く HTTP / WebSocket API
- 内部向け管理 API
- 将来の AaaS Public API

---

# 🧬 1. API デザイン基本方針

1. **Resource-Oriented（リソース指向）**
   - URL は「名詞」中心 `/habits`, `/projects`, `/users/{id}` など
2. **HTTPメソッドに意味を持たせる**
   - GET = 取得 / POST = 作成 / PUT = 全更新 / PATCH = 部分更新 / DELETE = 削除
3. **一貫した命名とレスポンス形式**
4. **すべて OpenAPI 3.1 で記述可能な形にする**
5. **“クライアントがシンプルに使えること”を最優先**

---

# 📍 2. ベース仕様

## 2.1 Base URL

- SaaS毎に基本パターンは：

https://api.{project-domain}/v1/…

- 内部・preview環境は：

https://api-stg.{project-domain}/v1/…

## 2.2 バージョニング

- URLバージョン（推奨）：`/v1/`, `/v2/`
- 非互換な変更が入るときのみ vUp  
- クエリでの `?version=` は使用しない

---

# 📚 3. URL 設計ルール（REST-ish）

## 3.1 リソース名

- 必ず **複数形の英語名詞** を使用（snake / kebab は使わない）
  - OK: `/users`, `/projects`, `/subscriptions`
  - NG: `/user-list`, `/getUsers`

## 3.2 パスの基本パターン

- 一覧：`GET /resources`
- 詳細：`GET /resources/{id}`
- 作成：`POST /resources`
- 更新：`PATCH /resources/{id}`
- 削除：`DELETE /resources/{id}`

## 3.3 関連リソース

- ネストは **2階層まで**：

GET /projects/{projectId}/members
POST /projects/{projectId}/invites

---

# 🧾 4. リクエスト / レスポンス形式

## 4.1 Content-Type

- 全ての JSON API は：
  - `Content-Type: application/json; charset=utf-8`

## 4.2 共通レスポンスラッパ（推奨）

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "requestId": "uuid",
    "timestamp": "2025-11-14T12:34:56Z"
  }
}

エラー時：

{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "email is invalid",
    "details": { "field": "email" }
  },
  "meta": { "requestId": "uuid", "timestamp": "..." }
}


⸻

⚠️ 5. エラー設計

5.1 HTTPステータス
	•	200 OK（成功）
	•	201 Created
	•	204 No Content
	•	400 Bad Request（バリデーション）
	•	401 Unauthorized
	•	403 Forbidden
	•	404 Not Found
	•	409 Conflict（重複など）
	•	429 Too Many Requests
	•	500 Internal Server Error

5.2 エラーコード例
	•	VALIDATION_ERROR
	•	AUTH_REQUIRED
	•	PERMISSION_DENIED
	•	NOT_FOUND
	•	CONFLICT
	•	RATE_LIMITED
	•	INTERNAL_ERROR

⸻

🔐 6. 認証 / 認可

6.1 認証方式
	•	基本：JWT + Bearer Token
	•	Authorization: Bearer <token>
	•	管理系 / Machine-to-Machine 用に API Key も許可
	•	X-API-Key: <key>

6.2 認可
	•	RBAC（Role-Based Access Control）
	•	ユーザーロール例：
	•	owner, admin, member, viewer
	•	Each endpoint に必要ロールを明記：

x-permissions:
  roles:
    - admin
    - owner


⸻

📄 7. OpenAPI 仕様（api_spec.yaml の標準）

7.1 ヘッダ

openapi: 3.1.0
info:
  title: {SaaS Name} API
  version: 1.0.0
servers:
  - url: https://api.{project-domain}/v1

7.2 スキーマ
	•	必ず components.schemas を用いて再利用：

components:
  schemas:
    User:
      type: object
      required: [id, email]
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
          nullable: true


⸻

🔁 8. Pagination / Filtering / Sorting

8.1 Pagination（cursorベース推奨）

GET /projects?limit=20&cursor=xxx

レスポンス：

{
  "success": true,
  "data": [...],
  "meta": {
    "nextCursor": "yyy",
    "hasMore": true
  }
}

8.2 Filtering

クエリパラメータ：

GET /tasks?status=done&assigneeId=xxx

8.3 Sorting

GET /tasks?sort=createdAt&order=desc


⸻

⏱ 9. 非同期処理 / ジョブ

重い処理は 即時レスポンス + ジョブID を返す：

POST /reports
→ 202 Accepted
{
  "success": true,
  "data": { "jobId": "..." }
}

進捗確認：

GET /jobs/{jobId}


⸻

📡 10. Webhook / Event

10.1 Webhook 基本仕様
	•	POST https://customer-endpoint に JSON 送信
	•	X-Signature ヘッダで HMAC 署名
	•	event フィールドで種類を示す：

{
  "id": "evt_123",
  "event": "subscription.created",
  "data": { ... },
  "createdAt": "..."
}


⸻

🧪 11. テストポリシー
	•	ユニットテスト：/api/tests/unit
	•	統合テスト：/api/tests/integration
	•	Contract Test：OpenAPI を基にモック生成
	•	TestGeneratorAgent が自動生成（将来）

⸻

🧠 12. エージェント用ルール（重要）

API/DBDesignAgent
	•	API 仕様書は必ず docs/api_spec.yaml に出力
	•	命名・エラー形式・認証は本ファイルに準拠

BackendAgent
	•	OpenAPI → 実装コードへのマッピングを行う
	•	実装と Spec が乖離した場合、Spec 修正案も出す

WebDevAgent / SwiftDevAgent
	•	クライアント側の型定義は api_spec.yaml を元に自動生成
	•	Magic string の直書きは禁止

⸻

🔒 13. 禁止事項
	1.	GET /doSomething のような 動詞主体の URL
	2.	200 OK だが body の中に "success": false だけ入れて失敗を表現
	3.	仕様書にないフィールドを勝手に追加
	4.	.env に APIキーを平文保存（Secrets管理に従うこと）
	5.	バージョンを上げないままレスポンス破壊的変更

⸻

🔮 14. 将来拡張（v2以降）
	•	GraphQL / tRPC 用 Standard
	•	Streaming API（Server-Sent Events, WebSocket）ポリシー
	•	AaaS Factory 公開API
	•	Rate Limit / Quota Policy

⸻

END