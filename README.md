AaaS Factory – GPT Project File Structure (v1)
================================================

# 📘 Purpose
このプロジェクトでは、SaaS/AaaS を自動生成するための
「マスターファイル（唯一の真理）」を整理し、  
GPT が役割ごとに正確に参照できるように構造化しています。

GPT Projects は正式なフォルダ機能を持たないため、  
**ファイル名に prefix を付けることで仮想的なフォルダ構成**を作成しています。

このルールに従うと、GPT が混乱せず、チャットごとの役割が明確になります。

---

# 📂 1. /master/  — Factory の中枢マスターファイル

(全 Factory の仕様を定義する唯一の真理)

master/
factory_master_v1.md
factory_automation_master_v1.md
factory_templates_master_v1.md
agent_roles_master_v1.md
agent_specs_master_v1.md
coding_guidelines_master_v1.md
design_system_master_v1.md
ui_kit_master_v1.md
api_standards_master_v1.md
data_modeling_master_v1.md
cicd_master_v1.md
infra_master_v1.md
saas_structure_master_v1.md

※ GPT Projects にアップロードするときは  
ファイル名の先頭に `master__` を付けるとさらに安定します。

例：  
`master__factory_master_v1.md`

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

# 📌 リネーム規則（重要）

GPT Projects のファイルはフォルダとして扱えないため  
**以下の命名ルールでアップロードしてください：**

master__factory_master_v1.md
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

# END