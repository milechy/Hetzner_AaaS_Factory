# saas_structure_master_v1.md
AaaS Factory – SaaS Project Structure Master (v1)  
最終更新: 2025-11-14

---

# 🎯 Purpose（目的）

このファイルは、AaaS Factory が生成する  
**すべての SaaS プロジェクトの統一構造（ディレクトリ / 命名規則 / ファイル分類）を定義した唯一の真理（SSOT）** である。

Factory のエージェントは、この構造を前提として  
- Next.js（Web）  
- SwiftUI（iOS）  
- Backend（API）  
- Infra（Docker / Coolify）  
- CI/CD  
を自動生成・自動修正・自動更新する。

---

# 🧩 1. SaaS プロジェクト全体の基本構造

SaaS-X（例：saas_1）は以下の 5 レイヤーで構成される。

saas_X/
├─ web/           (Next.js)
├─ api/           (Backend: FastAPI/Node)
├─ ios/           (SwiftUI)
├─ infra/         (Docker / Coolify / Terraform)
├─ docs/          (仕様書)
└─ .github/       (CI/CD)

各フォルダは Factory Templates と Design System に従い、  
WebDevAgent / SwiftDevAgent / BackendAgent / CICDAgent が自動生成する。

---

# 🖥️ 2. web/（Next.js）構造

web/
├─ app/
│   ├─ layout.tsx
│   ├─ page.tsx
│   ├─ dashboard/
│   │    ├─ page.tsx
│   │    └─ components/
│   ├─ settings/
│   │    └─ page.tsx
│   └─ (pages auto-created from spec)
│
├─ components/
│   ├─ primitives/   (DS Button, Input…)
│   ├─ composite/    (Card, Form…)
│   └─ patterns/     (DashboardShell, AuthLayout…)
│
├─ hooks/
├─ lib/
├─ public/
├─ types/
├─ utils/
└─ tailwind.config.js

### Must Rules
- **Design System Tokens を参照（CSS Variables）**  
- HTML 構造は UIDesignAgent の仕様に従う  
- API 呼び出しは `lib/api.ts` から行う  
- 新規ページは ArchitectAgent の IA に従う

---

# 🔧 3. api/（Backend）

api/
├─ src/
│   ├─ routers/
│   │    └─ (generated from api_spec.yaml)
│   ├─ services/
│   ├─ schemas/
│   ├─ db/
│   │    ├─ client.ts
│   │    └─ migration/
│   └─ utils/
│
├─ prisma/
│   ├─ schema.prisma
│   └─ migrations/
│
├─ tests/
│
├─ requirements.txt or package.json
└─ Dockerfile

### Must Rules
- すべてのルーターは `api_spec.yaml` から生成  
- DB schema は ERD から一貫性チェック  
- migrations はテンプレ基準 + 差分管理

---

# 📱 4. ios/（SwiftUI）

ios/
├─ App/
│   ├─ SaaSApp.swift
│   └─ AppRouter.swift
│
├─ Views/
│   ├─ DashboardView.swift
│   ├─ SettingsView.swift
│   └─ (generated views…)
│
├─ Components/
│   ├─ DSButton.swift
│   ├─ DSTextField.swift
│   └─ Card.swift
│
├─ Tokens/
│   ├─ ColorTokens.swift
│   ├─ FontTokens.swift
│   └─ Spacing.swift
│
├─ Networking/
│   ├─ ApiClient.swift
│   └─ AuthClient.swift
│
├─ Store/
│   ├─ AppStore.swift
│   └─ StateModels.swift
│
└─ Resources/
└─ Assets.xcassets

### Must Rules
- 色/フォント/spacing は Design System の Token をそのまま使用  
- アーキテクチャは MV（View + ViewModel）  
- API client は `api_spec.yaml` をもとに自動生成

---

# 🛠 5. infra/（Infra Template）

infra/
├─ docker-compose.yml
├─ coolify/
│   ├─ nextjs.json
│   └─ api.json
│
├─ terraform/
│   ├─ variables.tf
│   ├─ main.tf
│   └─ outputs.tf
│
└─ nginx/
└─ default.conf

### Must Rules
- docker-compose は TemplatesMaster を参照し自動生成  
- Coolify JSON はテンプレに従い、 Secrets は human 操作禁止  
- Terraform は base_server.tf を継承

---

# 📦 6. docs/（仕様書）

docs/
├─ requirements.md        (要件定義)
├─ design_system.md       (Design System の参照)
├─ ui_spec.md             (UIDesignAgent 出力)
├─ api_spec.yaml          (API/DBDesignAgent 出力)
├─ architecture.md        (ArchitectAgent 出力)
├─ infra.md               (InfraAgent 出力)
└─ CHANGELOG.md           (TemplateAgent / Self-Dev 出力)

### Must Rules
- すべての仕様変更は docs に保存  
- api_spec.yaml は “唯一のAPI真理”  
- UI関連は design_system_master を参照すること

---

# 🔁 7. .github/（CI/CD）

.github/
└─ workflows/
├─ nextjs.build.yml
├─ api.build.yml
├─ swift.build.yml
├─ deploy.yml
└─ checks.yml

### Must Rules
- CICDAgent が自動生成  
- runner-setup は TemplatesMaster 経由  
- 人間が workflow を手で編集するのは禁止

---

# 🧭 8. 命名規則（Naming Conventions）

## 8.1 SaaS プロジェクトの名前

saas_{number}
例）saas_1, saas_2, saas_3

## 8.2 ブランチ名

main
develop
feature/{task}
fix/{issue}

## 8.3 API

/api/{resource}/{action}

## 8.4 フォルダ命名

camelCase（components, hooks, utils）
PascalCase（SwiftUI Views）
snake_case（Terraform）

---

# 🧪 9. エージェントの使用ルール

各 Agent は常に次を守る：

### ManagerAgent  
→ このファイルを参照して新規 SaaS のディレクトリを作成する

### ArchitectAgent  
→ 機能を web/api/ios に振り分ける

### UIDesignAgent  
→ `/docs/ui_spec.md` を更新する

### WebDevAgent  
→ `/web` フォルダに従って生成

### BackendAgent  
→ `/api` に従って生成

### SwiftDevAgent  
→ `/ios` に従って生成

### CICDAgent  
→ `.github/workflows` を生成

### TemplateAgent  
→ すべての改善を `/templates` に昇格させる

---

# 🔒 10. 制約ルール（非常に重要）

1. SaaS の構造を “変えてはいけない”  
2. 変更が必要な場合は  
   → SaaS個別ではなく  
   → **Factory Templates に昇格させること**  
3. `.env` は禁止（Coolify Secrets を必ず使用）  
4. API spec は docs に保存し、コード自動生成の唯一ソースとして扱う  
5. デザイン変更は Design System vX に反映する  

---

# 🔮 11. 将来拡張（v2以降）

- Multi-tenant SaaS 構造  
- Plugin-based architecture  
- AI Agent integration directories  
- Microfrontend 対応  
- Edge deploy support（Vercel hybrid）  

---

## 7. 推奨画面パターン（square-ui 参照）

本セクションは「SaaSの初期設計で利用可能な典型パターン」をまとめたものである。  
ソースは square-ui の OSS テンプレートを参照しつつ、**構造のみ**採用する。

### 7.1 Dashboard
- KPI Cards（最大4〜6）  
- Recent Activity（Table）  
- Secondary Panels（Tasks / Notifications / Usage）

### 7.2 Email Viewer（Three-Pane Layout）
- Left：Folder/Labels  
- Middle：Email List  
- Right：Email Detail  
※ Pattern: DashboardShell + Nested Split Layout

### 7.3 Chat
- Left：Conversation List  
- Middle：Messages  
- Bottom：Input Area（AI Bot 対応も可）

### 7.4 Calendar
- Weekly View（time slots）  
- Monthly View（grid）  
- Event Detail Drawer

### 7.5 Tasks / Kanban
- Columns（Todo / Doing / Done）  
- Draggable Cards（UI Kit 標準ではないため、情報構造のみ参照）

### 7.6 Projects Timeline
- Vertical timeline  
- Phases / Milestones / Notes

### 7.7 使用上の注意
- square-ui の class / color / spacing は使用禁止  
- すべて Design System / UI Kit パターンに再マッピング  
- Web向けの IA 参考として利用  
- 作成したワイヤーフレームはこのチャット（UI/UXルーム）で管理する

---

# END