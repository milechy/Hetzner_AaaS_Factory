AaaS Factory – GPT Project File Structure (v1.3.7)
================================================

# 📘 Purpose
このプロジェクトでは、SaaS/AaaS を自動生成するための
「マスターファイル（唯一の真理）」を整理し、  
GPT が役割ごとに正確に参照できるように構造化しています。

# 🚀 Release Automation (Current)
フロー概要：
1. **main** ブランチで CHANGELOG.md に次バージョンのセクションを追加して commit
   例: `## [v1.3.7] - YYYY-MM-DD`
2. **その commit（= main の HEAD）に対して** `vX.Y.Z` タグを作成して push
3. GitHub Actions (`.github/workflows/release.yml`) が自動実行され、
   - CHANGELOG.md の該当セクションを抽出（Fail Fast: 無ければ即失敗）
   - `### SSOT` セクションを **重複なし** で自動付与
   - GitHub Release を自動作成

重要ルール：
- **タグより先に CHANGELOG.md を必ず commit する（順序厳守）**
- **タグは必ず main の HEAD を指す**（別ブランチ/古いコミットに付けない）
- 同一タグの再 push は基本禁止（やるなら「削除→付け直し」を手順化する）

## 🔖 Release Trigger Rule（重要）

- Release Workflow は **tag push のみ** をトリガーとする
- 通常の commit / push（main 含む）では Release は作成されない
- Release を作成したい場合は **必ず vX.Y.Z タグを push** する

## ✅ 正式な Release 手順（最短・確実）

```bash
# 0. main を最新にする
git checkout main
git pull origin main

# 1. CHANGELOG.md に次バージョンを追加して main に push
git add CHANGELOG.md
git commit -m "docs(changelog): add vX.Y.Z release notes"
git push origin main

# 2. "今の main の HEAD" に tag を切って push
git tag -a vX.Y.Z -m "vX.Y.Z – release"
git push origin vX.Y.Z
```

### リリース前の確認（30秒）

```bash
# タグ対象コミットに CHANGELOG のセクションが存在するか
TAG=vX.Y.Z
git show "${TAG}:CHANGELOG.md" | rg -n "^## \\\[${TAG//./\\.}\\] - "

# tag が main HEAD を指しているか
MAIN_HEAD=$(git rev-parse HEAD)
TAG_HEAD=$(git rev-parse "${TAG}^{ }")
[ "$MAIN_HEAD" = "$TAG_HEAD" ] && echo "OK: tag points to main HEAD" || echo "NG: tag does not point to main HEAD"
```

## 🚫 禁止事項（事故防止）

- ❌ CHANGELOG.md に無いバージョンの tag push
- ❌ main 以外のコミットに tag を付ける（別ブランチ/古い HEAD）
- ❌ tag を切った後に CHANGELOG を修正して「後追いで整合」を取ろうとする
- ❌ GitHub UI からの手動 Release 作成（再現性が壊れる）

## 🤖 Release Workflow の Fail Fast 仕様

以下の場合、Workflow は意図的に失敗します：

- CHANGELOG.md に該当バージョンが存在しない
- Release セクションのフォーマットが不正（`## [vX.Y.Z] - YYYY-MM-DD` を満たさない）
- tag と CHANGELOG のバージョン不一致

これは **安全装置** であり、修正後に「正しい手順で」やり直す設計です。

## 🧹 Release 失敗時のリカバリ手順（これだけ覚える）

```bash
# 0. main を最新にする
git checkout main
git pull origin main

# 1. 失敗した tag を消す（ローカル + リモート）
git tag -d vX.Y.Z || true
git push --delete origin vX.Y.Z || true

# 2. CHANGELOG.md を修正 → commit → push
git add CHANGELOG.md
git commit -m "docs(changelog): fix vX.Y.Z release notes"
git push origin main

# 3. 同じバージョンで tag を付け直して push
git tag -a vX.Y.Z -m "vX.Y.Z – release"
git push origin vX.Y.Z
```

## 🧠 Design Rationale

本リポジトリでは「Release = 宣言的イベント」として扱うため、
CHANGELOG.md を唯一の真理（SSOT）とし、
tag push を最終確定操作としています。

これにより：
- Release 内容の再現性
- 履歴の一貫性
- 自動化の安全性

を最大化しています。

---

# 📂 1. /master/  — Factory の中枢マスターファイル

(全 Factory の仕様を定義する唯一の真理)

master/
factory_master_v3.md
factory_automation_master_v1.md
factory_templates_master_v1.md
agent_roles_master_v3.md
agent_specs_master_v1.md
coding_guidelines_master_v1.md
design_system_master_v1.md
ui_kit_master_v1.md
api_standards_master_v1.md
data_modeling_master_v1.md
cicd_master_v2.md
infra_master_v1.md
saas_structure_master_v1.md
master__security_checklist_v3.md
master__open_pr_contract_v1_3.md

※ GPT Projects にアップロードするときは  
ファイル名の先頭に `master__` を付けるとさらに安定します。

例：  
`master__factory_master_v3.md`

---

# 📂 2. /saas/ — 各 SaaS 専用仕様ファイル（個別）

saas/
saas_1_requirements_v1.md
saas_1_ui_spec_v1.md
saas_1_api_spec_v1.yaml
saas_1_db_design_v1.md
saas_1_cicd_v1.yaml

saas_2_requirements_v1.md
saas_2_ui_spec_v1.md
…

命名ルール：
- `saas_{number}_{type}_v{version}`

例：  
`saas_3_api_spec_v1.yaml`

---

# 📂 3. /factory/ — Factory 自身の自動改善ログ & デルタ

factory/
factory_change_log_v1.md
factory_improvement_suggestions.md
factory_diff_master_updates.md

用途：
- Factory Self-Dev チャットで発生する改善提案や、  
  マスターの差分（diff）をここに保存。

---

# 📂 4. /templates/ — テンプレ昇格されたコード/構造

templates/
nextjs_template_v1.md
swiftui_template_v1.md
api_template_v1.md
db_template_v1.md
infra_template_v1.md
cicd_template_v1.md

TemplateAgent が “共通化できるパターン” を抽出した時、  
テンプレートがここに入る。

---

# 📂 5. /infra/ — インフラ構成

infra/
docker_compose_template.md
coolify_config_template.md
terraform_template.md
hetzner_runner_setup.md

InfraAgent が生成するセットアップ系のファイル群。

---

# 📂 6. /ui/ — UI構造図・コンポーネント定義

ui/
wireframe_saas_1_v1.md
component_list_v1.md
design_token_map.md

UIDesignAgent の成果物を格納。

---

# 📂 7. /api/ — API仕様と補助ファイル

api/
openapi_saas_1_v1.yaml
openapi_saas_2_v1.yaml
api_endpoint_index.md

---

# 📂 8. /db/ — DB/ERD/Prisma 関連

db/
erd_saas_1_v1.md
prisma_saas_1_schema.prisma
migration_notes.md

---

# 📝 9. /docs/ — 全体ドキュメント

docs/
project_overview.md
factory_architecture_diagram.md
glossary.md

---

# 🔐 v1.3 Open-PR Contract（SSOT）

Pull Request の自動作成（Open PR）に関する **正式な SSOT 契約** は、
以下のマスターファイルに切り出して定義されている。

- **master__open_pr_contract_v1_3.md**

本 Contract は、Agent / CLI / ToolGate / Human Approval / GitHub API の
すべてに優先して適用される。

README は概要のみを記載する（正本は SSOT）。主な要点：
- **humanApproved=true** と **有効な Approval Token** がない限り write は実行しない
- Token scope は repo/baseBranch/proposalHash に拘束し、**actorId 一致を強い必須条件**として扱う
- GitHub API 401/403 は **Fail Safe** で扱い、常に PR 作成用の fallback URL を返す

---

# 📌 リネーム規則（重要）

GPT Projects のファイルはフォルダとして扱えないため  
**以下の命名ルールでアップロードしてください：**

master__factory_master_v3.md
master__ui_kit_master_v1.md
saas__1__requirements_v1.md
saas__1__ui_spec_v1.md
factory__diff__2025_11_14.md
infra__docker_compose_template.md
ui__wireframe__saas1_v1.md

---

# 🎯 GPT に読ませる指示方法

チャット開始時に：

すべての “master__” ファイルを読み込んでください。
また、必要に応じて “templates__” を参照してください。
SaaS-1 の作業時には “saas__1__*” ファイルも読み込んでください。

GPT が確実にフォルダ（prefix）を理解します。

---

# ✅ Current State
- Latest Release: v1.3.7
- Release Notes Source of Truth: CHANGELOG.md
- Release Workflow: .github/workflows/release.yml
- Status: Fully automated (tag-push) / Fail Fast on mismatch
- Recovery: Delete tag → fix CHANGELOG → re-tag (documented above)

---

# END
