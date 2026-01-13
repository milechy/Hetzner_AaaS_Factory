# Factory Master v3
最終更新: 2025-12

## 0. 最上位決定（憲法）

本 AaaS 自動開発ファクトリーの中核実行基盤は  
**OpenAI Agents SDK** とする。

- Agent 実行
- Tool 呼び出し
- Handoff / Review / Loop
は Agents SDK を前提に設計・実装する。

LangGraph は以下の場合のみ補助的に使用可能：
- 並列分岐が多い
- 明示的な状態遷移の可視化が必要
- SDK の直列 orchestration では表現困難な場合

LangFlow は中核に含めない。

---

## 1. Factory の本質

- Factory は「コードを書く AI」ではない
- **PR を生成・レビュー・進化させる自動開発基盤**である
- SSOT（master__*.md）が唯一の真実

---

## 2. 実行モデル

Factory は以下のループで動作する：

Plan → Execute → Review → Reflect

各フェーズは Agent SDK 上の Agent と Tool により実現される。

### Decision / Execution Separation

- Decision Layer: Human + GPT Project (Factory Self-Dev / PM)
- Execution Layer: VS Code Agent mode / GitHub Copilot Agent mode
- 実行ツールは独自に意思決定を行ってはならず、PR-firstルールをバイパスしてはならない。

---

## 3. 禁止事項

- SSOT を bypass する自動更新
- Agent による直接 push / merge
- 実行環境への直接操作（Shell / OS）

すべて PR / Tool / Gate 経由で行う。