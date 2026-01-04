````markdown
# Future Model Pool Master v1  
ファイル名: master__future_model_pool_v1.md  
最終更新: 2025-12-04  

---

## 0. 目的

本ドキュメントは、AaaS 自動開発ファクトリーが利用する  
**LLM モデル群（model pool）の公式リストと役割分担**を定義する。

ゴール:

- SelfDevAgent / 各エージェントが **モデル非依存 (model-agnostic)** に振る舞えるようにする
- タスク種別ごとに「どのモデルを優先するか」を明文化する
- 新しいモデル（例: MiniMax M2）を **安全に候補プールへ追加** できるようにする

---

## 1. モデル分類

### 1.1 カテゴリ

- **planner**: 企画・分解・設計（Intent → Plan）
- **codegen**: コード生成・リファクタ・修正
- **reviewer**: レビュー・査読・ジャッジ（multi-judge）
- **docgen**: ドキュメント生成・要約
- **reasoning**: 長文推論・仕様整理

1つのモデルが複数カテゴリを兼ねることもある。

---

## 2. モデルプール一覧（v1）

### 2.1 GPT-5.1 (OpenAI)

- id: `gpt-5.1`
- status: `primary`
- roles:
  - planner
  - codegen
  - reviewer
  - docgen
  - reasoning
- strengths:
  - 安定した推論
  - 長めのコンテキスト
  - PR説明文や仕様文の生成が得意
- weaknesses:
  - コスト高め
  - 超大規模コード一括生成では他モデルに譲る場合あり
- default_usage:
  - SelfDevAgent の **デフォルト planner**
  - ContextBuilder の要約
  - PR body / docs 生成
  - Reviewer layer の “最終判断役”

---

### 2.2 Claude 3.7 Sonnet

- id: `claude-3.7-sonnet`
- status: `primary`
- roles:
  - planner
  - codegen
  - reviewer
  - docgen
  - reasoning
- strengths:
  - 長文仕様の理解
  - コードベースの構造把握
  - 説明の丁寧さ
- weaknesses:
  - 一部 API 制約
- default_usage:
  - 大きめのコード変更の **レビュー役**
  - master__ 系ドキュメントのリライト
  - 仕様書 → 実装方針へのブリッジ

---

### 2.3 Grok-4

- id: `grok-4`
- status: `secondary`
- roles:
  - codegen
  - reviewer
- strengths:
  - コード生成が高速
  - 大胆な修正案
- weaknesses:
  - 出力の揺れが他モデルより強い場合がある
- default_usage:
  - 小さめのコード修正
  - 境界ケースや “別視点” のレビュー
  - multi-judge reviewer の **サブジャッジ**

---

### 2.4 DeepSeek Coder

- id: `deepseek-coder`
- status: `primary`
- roles:
  - codegen
- strengths:
  - コード生成に特化
  - 速度とコストのバランスが良い
- weaknesses:
  - 自然言語ドキュメントの生成には向かない
- default_usage:
  - WebDevAgent / BackendDevAgent / SwiftDevAgent の  
    **コード生成段階の第一候補**
  - テストコードの自動生成

---

### 2.5 MiniMax M2 REAP 162B (候補モデル)

- id: `minimax-m2-reap-162b-a10b`
- status: `experimental`
- provider: Cerebras / MiniMax
- roles (候補):
  - codegen
  - reasoning
- strengths (期待値ベース):
  - 大規模モデルによる強力な推論
  - コード理解・長文 reasoning
- weaknesses / 注意点:
  - 推論コスト・レイテンシ
  - 利用API / インフラ要件が未確定（2025-12 時点）
- default_usage (試験的):
  - SelfDevAgent v4 の **重要タスク時の second-opinion**
  - 大きな refactor 計画時の “advisor” 的利用
- policy:
  - `experimental` として扱い、  
    - ① 明示的に要求されたタスク  
    - ② SelfDevAgent の “high_risk” タスク  
    以外では使用しない
  - rollout 前に **小規模な検証タスク (PoC)** を必須とする

---

## 3. モデル選択ポリシー（全体）

1. **planner / high-level design**
   - 第一候補: `gpt-5.1`
   - 第二候補: `claude-3.7-sonnet`

2. **codegen（通常のコード生成）**
   - 第一候補: `deepseek-coder`
   - 第二候補: `gpt-5.1`
   - 特殊ケース: `grok-4`（高速実験）

3. **reviewer（multi-judge）**
   - core set:
     - `gpt-5.1`
     - `claude-3.7-sonnet`
     - `grok-4`

4. **docgen / spec**
   - 第一候補: `gpt-5.1`
   - 第二候補: `claude-3.7-sonnet`

5. **experimental / advanced reasoning**
   - 候補: `minimax-m2-reap-162b-a10b`
   - フラグ `allow_experimental_models=true` のときのみ使用

---

## 4. SelfDevAgent / 各エージェントへの露出

- 直接モデル ID をベタ書きせず、  
  すべて **`ModelSelector` / `LLMRouter`** を経由して利用する
- エージェントが使うのは **「モデルIDではなく “profile”」** である

例:  

```jsonc
{
  "profile": "codegen_standard",
  "requirements": {
    "language": "python",
    "max_tokens": 2048,
    "latency_sensitivity": "medium",
    "allow_experimental": false
  }
}
````

→ これに対して ModelSelector が
`deepseek-coder` or `gpt-5.1` を返す。

---

## 5. バージョン管理ポリシー

* このファイルは `future_model_pool` の SSOT とする
* モデルの追加 / 削除 / status変更 は必ず PR 経由で行い、

  * `master__future_model_pool_v2.md` 以降に履歴を残す
* SelfDevAgent v4 の LLM routing spec は
  常に最新の model_pool に従うこと

---

# END

````

---