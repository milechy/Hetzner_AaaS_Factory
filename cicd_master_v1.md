# cicd_master_v1.md
AaaS Factory – CI/CD Standards Master (v1)  
最終更新: 2025-11-14

---

# 🎯 Purpose（目的）

本ファイルは AaaS Factory の **CI/CD（自動ビルド・自動テスト・自動デプロイ）に関するすべての規約・構成・命名・パイプライン** を定める  
唯一の真理（SSOT）である。

対象：
- GitHub Actions（workflow）
- self-hosted runner（Hetzner / Mac）
- build/test/deploy の各段階
- lint / formatting / migrations
- Coolify / Docker deploy
- テストポリシー

Factory の CICDAgent / InfraAgent は 100% この文書に従って動く。

---

# 🧩 0. 全体構成（Pipeline Overview）

Developer / Agent
↓ push
GitHub Repository
↓
GitHub Actions (CI)
├─ lint
├─ type-check
├─ test (API/Web/Swift)
├─ build (Next.js / API / iOS)
├─ docker build
└─ deliver artifacts
↓
Coolify / Hetzner (CD)
↓
Deploy to Prod / Staging

ランナーは：

- **Hetzner Runner** → Web + API ビルド  
- **Mac Runner** → iOS ビルド（Fastlane）

---

# 🟦 1. Workflow 構造ルール（共通）

## 1.1 workflow ファイル名

.github/workflows/
├─ ci_web.yml
├─ ci_api.yml
├─ ci_ios.yml
├─ deploy_web.yml
├─ deploy_api.yml
├─ deploy_ios.yml
└─ checks.yml

## 1.2 workflow トリガー

on:
push:
branches: [ main, develop ]
pull_request:
workflow_dispatch:

## 1.3 Secrets の扱い（厳格）

- **GitHub Secrets を唯一の許可ストア**  
- `.env` は作らない  
- Coolify Secrets と同期  
- runner に secret を渡す際は `secrets.*` を使用  
- 明示的に `echo` やログ出力禁止

---

# 🟩 2. Lint / Test / Type-check（Quality Gate）

CI は以下の順序で実行：

	1.	Lint
	2.	Type-check (TS/Swift/Python)
	3.	Unit Test
	4.	Integration Test
	5.	Build

すべて通らない限り Deploy は行わない。

---

# 🟧 3. CI: Web（Next.js）

## 3.1 ci_web.yml

```yaml
name: Web CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  web-ci:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"

      - run: npm ci

      - run: npm run lint
      - run: npm run type-check
      - run: npm test --if-present

      - run: npm run build

      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: web-dist
          path: .next

3.2 Build Rules
	•	npm ci を基本
	•	Next.js は output: standalone
	•	Tailwind CLI ビルドを必須
	•	env は Coolify で注入（Actionsでは設定しない）

⸻

🟥 4. CI: API（FastAPI / Node）

4.1 ci_api.yml

name: API CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  api-ci:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - run: pip install -r api/requirements.txt

      - run: pytest api/tests

      - run: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

API Additional Rules
	•	OpenAPI に完全準拠
	•	migration 実行前に dry-run
	•	Prisma → npx prisma generate を実行

⸻

🟫 5. CI: iOS（SwiftUI）

5.1 Runner
	•	自宅Mac（24/365） or MacStadium
	•	Xcode CLI tools 必須

5.2 ci_ios.yml

name: iOS CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  ios-ci:
    runs-on: self-hosted-mac
    steps:
      - uses: actions/checkout@v4

      - name: Select Xcode
        run: sudo xcode-select -s /Applications/Xcode.app

      - name: Build App
        run: xcodebuild -scheme SaaSApp -destination 'platform=iOS Simulator,name=iPhone 15' build

iOS Build Rules
	•	Fastlane は deploy 時に実行
	•	CI ではビルド通過が最低条件
	•	Secrets は keychain に事前登録

⸻

🟪 6. Docker Build（共通）

docker_build.yml（自動生成）

name: Docker Build

on:
  workflow_call:

jobs:
  docker-build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: docker build -t ${{ env.IMAGE }} .

      - name: Push
        run: docker push ${{ env.IMAGE }}


⸻

🟦 7. CD: Coolify Deploy

CD は Coolify API を叩いてデプロイする。

deploy_web.yml

name: Deploy Web

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - name: Trigger Coolify Deploy
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_KEY }}" \
            https://coolify.{DOMAIN}/api/v1/deploy/web

deploy_api.yml も同様

⸻

🟥 8. Caching Strategy（重要）

Next.js / API / Swift でキャッシュ戦略は次：
	•	Node modules → actions/setup-node の cache
	•	Python venv → 無し（汚染回避）
	•	Swift build → derived data を runner側で保持
	•	Docker → layer cache 有効

⸻

📘 9. Runner Standardization（統一仕様）

9.1 2種類の Runner を使用
	1.	Hetzner Runner（Linux）
	•	Node.js build
	•	Python build
	•	Docker
	•	Deploy
	2.	Mac Runner（macOS）
	•	Swift build
	•	Fastlane deploy
	•	iOS signing

9.2 ランナーの配置

/srv/runner/
 ├─ run.sh
 ├─ config.sh
 └─ _work/

Mac側：

~/actions-runner/
 └─ run-ios.sh

9.3 ランナー登録

→ CICDAgent のみ が登録可能（人間操作は最小）

⸻

🧯 10. CI/CD における禁止事項
	•	workflow を手で編集（必ず CICDAgent 経由）
	•	Secrets をログ出力
	•	main 直接 push
	•	.env を作る
	•	docker build で root 起動
	•	deploy 前にテストをスキップ
	•	仕様書（api_spec.yaml）とズレた API を build
	•	iOS の署名ファイルを Git に保存

⸻

🔁 11. すべての SaaS がこの構造に従う（最重要）

SaaS-1 も SaaS-99 も、
CI/CD は完全同一構造で生成される。

CICDAgent のアルゴリズム：
	1.	saas_structure_master を読む
	2.	coding_guidelines_master を読む
	3.	cicd_master（本ファイル）を読む
	4.	SaaS 情報から 6種類の workflows を自動生成
	5.	仕様変更があれば再生成
	6.	TemplateAgent に昇格できる改善を提案

⸻

🔮 12. 将来拡張（v2）
	•	Canary Deploy
	•	Blue-Green Deploy
	•	Preview環境自動生成（PRごと）
	•	E2Eテスト Agent
	•	Performance Test Agent
	•	Sentry / Datadog 連携
	•	Multi-region deploy
	•	Infrastructure Drift Detection Agent

⸻

END