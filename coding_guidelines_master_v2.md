# coding_guidelines_master_v2.md
AaaS Factory – Coding Guidelines Master (v2)
最終更新: 2025-12-24

---

# 🎯 Purpose（目的）
本ファイルは AaaS Factory が生成する **すべてのコードと生成プロセス**の品質・安全性の唯一の真理（SSOT）である。
v2 では “生成プロセス規約（Agent/Tool・PR-only・LLM routing・high-risk）” を正式に追加する。

---

# 🧩 0. 基本原則（全言語共通）
（v1 を踏襲）
1. 可読性 > 短距離の最適化
2. 早期リターンを優先
3. 関数は小さく、1つの責務
4. 命名は意図が理解できる名前
5. Magic Number / Magic String 禁止
6. 例外処理を明示的に書く
7. コメントは “なぜ” を書く
8. テストしやすい構造を優先
9. マスター文書との差異があればマスターを優先
10. Factory Templates を必ず参照すること

---

# 🔒 0.1 生成プロセス規約（v2 追加・必須）

## 0.1.1 Agent / Tool 分離
- Agent = 判断・計画
- Tool = 実行
- Agent が直接行うことは禁止：
  - git write / push / merge
  - infra change
  - secret 操作

## 0.1.2 PR-only Change
- 変更は “PullRequestProposal(JSON)” として提案すること。
- 自動でリポジトリへ書き込む実装は禁止（v0では提案で停止）。

## 0.1.3 LLM Routing（モデル非依存）
- model ID の直指定は禁止
- Agent は profile のみ指定
- **必ず LLMRouter を経由**
- high-risk（infra/security/billing/template）を low-cost model に割り当てることは禁止（Router 側責務）

## 0.1.4 High-risk ドメインの扱い（v0）
- v0 実装では high-risk の “ファイル生成” は行わない
- Skeleton は生成して良い（合意事項）
- PullRequestProposal には以下を必須：
  - `risk.highRiskDetected=true`
  - `risk.notes` に根拠
  - `validation.manualSteps` に human gate 要求
  - `changes.files` に high-risk のファイルを含めない

---

# 🟦 1. TypeScript / Next.js
（v1 を踏襲。省略）

---

# 🟩 2. Python（FastAPI / Scripts）
（v1 を踏襲。省略）

---

# 🟨 3. Swift / SwiftUI（iOS）
（v1 を踏襲。省略）

---

# 🟥 4. Database（Prisma / SQL）
（v1 を踏襲。省略）

---

# 🟫 5. Dockerfile / Infra / YAML
（v1 を踏襲。省略）
※ v0 では infra change 自体を実行しない。提案のみ。

---

# 🧪 7. テストの基準
（v1 を踏襲。省略）

---

# 🧯 8. 禁止事項（v2 追加）
- Agent が model ID を指定すること
- Agent が git write / infra change / secret 操作を行うこと
- high-risk ドメインの変更を v0 でファイル生成すること
- PR 提案なしで変更を適用すること

---

END