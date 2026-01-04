# data_modeling_master_v1.md
AaaS Factory – Data Modeling & DB Standards Master (v1)  
最終更新: 2025-11-14

---

# 🎯 Purpose（目的）

本ファイルは AaaS Factory における

- データモデリング（ERD）
- Prisma / SQL スキーマ設計
- マイグレーション運用
- Multi-tenant の前提
- ID / timestamp / soft delete
- リレーション / インデックス設計

に関する **唯一の真理（SSOT）** である。

対象：
- API/DBDesignAgent
- BackendAgent
- TemplateAgent
- SelfDevAgent

---

# 🧩 0. 基本原則

1. **シンプルで読みやすい ERD**  
2. **API仕様（OpenAPI）と常に整合する DBモデリング**  
3. **Prisma（ORM）を第一クラス市民として扱う**  
4. **すべてのモデルに ID / createdAt / updatedAt を必須**  
5. **将来の Multi-tenant に対応できる拡張性**  
6. **Migration は必ず自動生成・履歴管理**  
7. **生 SQL の直書きは最小限に抑える**

---

# 🧠 1. データモデルの基本形（全テーブル共通）

各モデルは最低限、次のフィールドを持つ：

```text
id          : 主キー（UUID）
createdAt   : 作成日時
updatedAt   : 更新日時
deletedAt?  : 論理削除用（soft delete）

Prisma 例：

model Example {
  id        String   @id @default(uuid())
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  deletedAt DateTime?
}


⸻

🪪 2. ID / 主キー / 外部キー ポリシー

2.1 主キー
	•	すべてのテーブルで 単一主キー（UUID string） を基本とする
	•	数値オートインクリメントは原則使用しない（分散環境前提）

2.2 外部キー
	•	外部キーは {参照先モデル}Id という命名にする

例：

model Project {
  id        String   @id @default(uuid())
  ownerId   String
  owner     User     @relation(fields: [ownerId], references: [id])
}


⸻

👥 3. Multi-tenant 対応（将来を見据えた設計）

v1では「単一テナント前提 + tenant対応しやすい形」にする。

3.1 テナント識別の考え方
	•	将来、テナント単位でデータ分離が必要になった場合のために
tenantId（String）を追加できる余地を残す
	•	Multi-tenant化が必要なモデルは、tenantId を追加した v2 モデルにする

例（v2想定）：

model Project {
  id        String   @id @default(uuid())
  tenantId  String
  ownerId   String
  ...
}


⸻

📚 4. モデル命名ルール

4.1 Prisma / ERD モデル
	•	単数形の PascalCase（User, Project, Subscription）
	•	DB上のテーブル名は自動的に複数形（users, projects）

model User {
  id String @id @default(uuid())
}

4.2 フィールド名
	•	camelCase（createdAt, ownerId, isActive）
	•	boolean フィールドは is / has / can で始める

⸻

🧩 5. 関連（Relations）設計

5.1 1:n

model User {
  id       String    @id @default(uuid())
  projects Project[]
}

model Project {
  id      String @id @default(uuid())
  ownerId String
  owner   User   @relation(fields: [ownerId], references: [id])
}

5.2 n:n
	•	中間テーブル（明示）を使うことを推奨

model User {
  id          String          @id @default(uuid())
  memberships ProjectMember[]
}

model Project {
  id          String          @id @default(uuid())
  members     ProjectMember[]
}

model ProjectMember {
  id        String   @id @default(uuid())
  userId    String
  projectId String

  user      User     @relation(fields: [userId], references: [id])
  project   Project  @relation(fields: [projectId], references: [id])

  @@unique([userId, projectId])
}


⸻

🗂 6. インデックス / パフォーマンス

6.1 インデックスルール
	•	外部キー + 検索に使用するフィールドにインデックスを追加
	•	Prisma では @@index を使用

model Task {
  id        String @id @default(uuid())
  projectId String
  status    String

  @@index([projectId])
  @@index([status])
}

6.2 ユニークキー
	•	メールアドレスなどは @unique
	•	複合ユニークは @@unique([col1, col2])

⸻

📄 7. ER 図（テキスト表現ルール）

API/DBDesignAgent は ER 図を「テキストフォーマット」で docs に出力する：

[User] 1 - n [Project]
[Project] 1 - n [Task]
[User] n - n [Project] via [ProjectMember]

	•	ERDは必ず docs/db_design.md に保存
	•	ERD ⇔ Prisma ⇔ OpenAPI を自動整合させる

⸻

💾 8. Prisma スキーマ設計ポリシー

8.1 ファイル構成

api/prisma/
 ├─ schema.prisma
 └─ migrations/

8.2 デフォルトフィールド

model BaseModel {
  id        String   @id @default(uuid())
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  deletedAt DateTime?
}

※ Prisma は継承がないため、パターンとして BaseModel を意識し、
各モデルに同様のフィールドを持たせる。

⸻

🔁 9. Migration 運用ルール

9.1 生成
	•	Prisma の migrate dev / migrate deploy を使用
	•	直接 SQL を書かない（特殊なケースを除く）

9.2 命名規則

YYYYMMDDHHMM_add_users_table
YYYYMMDDHHMM_add_project_member_unique
YYYYMMDDHHMM_modify_task_status_enum

9.3 本番適用
	•	CI に組み込み可能だが、最初は手動 or cron を推奨
	•	重大な schema 変更は SelfDevAgent がレビュー しても良い

⸻

🧪 10. Data Validation / Enum

10.1 Enum の使い方
	•	状態フィールド（status, role, type）は enum 使用

enum TaskStatus {
  TODO
  IN_PROGRESS
  DONE
}

	•	API側の enum と Prisma enum を必ず同期
	•	enum定義は api_standards_master_v1.md と整合

⸻

🧯 11. データ削除ポリシー（Soft Delete）

基本方針：Soft Delete を優先（削除履歴を残す）
	•	deletedAt が null → 有効
	•	deletedAt に値 → 論理削除済み

API 側：
	•	通常の一覧取得は deletedAt IS NULL 前提
	•	完全削除は管理画面 or メンテナンス用ジョブ

⸻

🔐 12. セキュリティ / PII
	•	パスワードは passwordHash として保存（生パスワード禁止）
	•	PII（email, name, address）は 必要最小限
	•	ログには PII を出力しない
	•	暗号化が必要なフィールドがある場合、encrypted_* 命名にする

⸻

📊 13. Factory 共通モデル（共通テーブル）

複数 SaaS で共有されうるモデルは、テンプレートとして標準化する：
	•	User / Account
	•	Subscription / Plan
	•	Project / Team
	•	AuditLog（ユーザー操作ログ）

TemplateAgent は、複数SaaSで似たモデルが現れた場合、
共通モデルとしてテンプレに昇格させることができる。

⸻

🧠 14. API/DBDesignAgent の行動ルール
	1.	api_standards_master_v1.md を読み、API仕様を設計
	2.	本ファイル data_modeling_master_v1.md を読み、DB設計を行う
	3.	Prisma スキーマを生成
	4.	ERD を docs/db_design.md に書き出す
	5.	仕様変更があれば ERD / Prisma / OpenAPI を 同時に更新案として提示

⸻

🧱 15. BackendAgent の行動ルール
	•	Prisma schema → DB migration → repository 実装 → service 実装
	•	Model 名・フィールド名はこの Master に従う
	•	手書き SQL は最小限（raw query が必要な場合のみ）
	•	仕様差分があれば、API/DBDesignAgent にフィードバック

⸻

🔒 16. 禁止事項
	•	自動生成以外の migration 手書き（原則禁止）
	•	Prisma schema と OpenAPI がズレた状態でデプロイ
	•	ID に連番 int を使う（分散環境非対応）
	•	外部キー無しの孤児テーブル
	•	SELECT * の常用
	•	PII をログに出力
	•	deletedAt を使わず物理削除乱発

⸻

🔮 17. 将来拡張（v2 以降）
	•	本格 Multi-tenant（tenantId / row-level isolation）
	•	Event Sourcing / Audit log テンプレ
	•	Time-series data 用ストアルール
	•	Data Warehouse / Analytics パイプライン
	•	PII 暗号化ポリシー詳細
	•	Partition / Sharding 戦略

⸻

END