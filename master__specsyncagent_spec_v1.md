# SpecSyncAgent Specification v1  
Intent Engine Integration  
最終更新: 2025-11-19

---

# 0. 目的

SpecSyncAgent はユーザーの要求・SaaS仕様を  
**Intent 正規化 → 構造化仕様 → API / DB / UI / Flow**  
に変換し、リポジトリへ同期する。

---

# 1. Intent → Structured Spec 変換

SpecSyncAgent は自然言語仕様から以下を抽出する：

1. Entities  
2. Actions（CRUD / workflows）  
3. Constraints  
4. UI Flows  
5. Dataflows  
6. Integration Points  
7. API definitions  
8. DB models  
9. Non-functional requirements  

---

# 2. Intent Normalization Pipeline

SelfDevAgent v2 と同じ Intent Engine を実装：

- Rewrite  
- Decompose  
- Interpret  
- Validate（master__ との照合）

SpecSyncAgent はこれを仕様書生成用に再構成する。

---

# 3. Structured Specification Format

SpecSyncAgent は最終的に以下の JSON を出力する：

```json
{
  "entities": [],
  "actions": [],
  "constraints": [],
  "ui_flows": [],
  "dataflows": [],
  "api_endpoints": [],
  "db_models": [],
  "integration_points": [],
  "nfr": []
}
````

---

# 4. リポ同期方法

SpecSyncAgent は以下を生成する：

* `docs/spec/api.md`
* `docs/spec/db.md`
* `docs/spec/ui.md`
* `docs/spec/entities.json`

同期方法：

* PR 生成（自動）
* drift 発生時は TemplateAgent と連携
* master（SSOT）と矛盾があれば更新案を作る

---

# 5. 安全ガード

SpecSyncAgent は：

* data_modeling_master
* api_standards_master
* design_system_master
  と照合し、矛盾がある場合は必ず警告を出す。

---

# END

````

---