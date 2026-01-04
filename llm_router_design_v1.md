￥````markdown
# LLMRouter / ModelSelector Design v1  
ファイル名: llm_router_design_v1.md  
関連マスター:
- master__future_model_pool_v1.md
- master__selfdevagent_llm_routing_v1.md

最終更新: 2025-12-05  

---

## 0. 目的

本ドキュメントは、AaaS 自動開発ファクトリー内で利用する

- **LLMRouter**
- **ModelSelector**

の設計を定義する。

役割:

- SelfDevAgent v4 や各エージェントが **「モデル名」ではなく「目的（profile）」を指定するだけ** で最適な LLM を使えるようにする
- `master__future_model_pool_v1.md` に定義された **モデル一覧** と  
  `master__selfdevagent_llm_routing_v1.md` に定義された **profile / routing spec** をもとに、
  実際の `model_id` を選択する

重要な方針:

- **model-agnostic（モデル非依存）**  
- **config-driven（マスターがSSOT）**  
- **fallback-aware（障害時の自動切替が可能）**

---

## 1. 全体アーキテクチャ

### 1.1 コンポーネント構成

```text
+---------------------+        +--------------------------+
|  SelfDevAgent v4    |        |  Worker / Meta Agents   |
|  Planner / Executor |        |  (WebDev, Backend, etc) |
+----------+----------+        +-------------+-----------+
           |                                    |
           | 1) profile + requirements          |
           v                                    v
     +-----+--------------------------------------+
     |           LLMRouter / ModelSelector        |
     |                                            |
     | - ModelSelector                           |
     | - RoutingPolicy                           |
     | - ModelPool (loaded from master__)        |
     +------------------+------------------------+
                        |
                        | 2) model_id + fallback
                        v
                +-------+--------+
                |    LLMClient   |
                |  (GPT, Claude, |
                |   Grok, etc.)  |
                +----------------+
                        |
                        v
                   LLM Provider
````

### 1.2 想定配置

* コード:

  * `infra/llm/model_pool_loader.py`
  * `infra/llm/model_selector.py`
  * `infra/llm/router.py`
  * `infra/llm/clients/*.py` （GPT/Claude/Grok/DeepSeek など）

* テスト:

  * `tests/infra/llm/test_model_selector.py`
  * `tests/infra/llm/test_llm_router.py`

---

## 2. データモデル

### 2.1 ModelConfig（1モデルを表す構造体）

`master__future_model_pool_v1.md` をもとに、ランタイムで扱う形。

```python
@dataclass
class ModelConfig:
    id: str                     # 例: "gpt-5.1"
    status: Literal["primary", "secondary", "experimental"]
    roles: list[str]            # ["planner", "codegen", "reviewer", ...]
    provider: str               # "openai" / "anthropic" / "xai" / "deepseek" / "minimax" etc.
    context_window: int         # 最大トークン数
    cost_tier: Literal["low", "medium", "high"]
    latency_tier: Literal["low", "medium", "high"]
    notes: str | None = None
```

### 2.2 ModelPool

```python
@dataclass
class ModelPool:
    models: dict[str, ModelConfig]  # key = model_id

    def get_by_role(self, role: str) -> list[ModelConfig]:
        ...

    def get(self, model_id: str) -> ModelConfig | None:
        ...
```

#### ロード方法（v1）

* 起動時に `master__future_model_pool_v1.md` の対応する YAML/JSON 相当を読み込む or 静的に埋め込む
* 将来的には `master__` を RAG / 内部API経由で読む方針だが、v1ではコード側に一旦定義してOK

---

## 3. 入力仕様（Selection Request）

SelfDevAgent やエージェントは、**直接 model_id を指定しない**。
代わりに `LLMSelectionRequest` を渡す。

```python
@dataclass
class LLMSelectionRequirements:
    task_kind: Literal["planner", "codegen", "reviewer", "docgen", "reasoning"]
    language: str | None = None                    # "python", "typescript" etc.
    max_tokens: int | None = None                  # 必要なら
    latency_sensitivity: Literal["low", "medium", "high"] = "medium"
    cost_sensitivity: Literal["low", "medium", "high"] = "medium"
    risk_level: Literal["low", "normal", "high"] = "normal"
    allow_experimental: bool = False

@dataclass
class ContextStats:
    approx_input_tokens: int
    approx_output_tokens: int

@dataclass
class LLMSelectionRequest:
    profile: str                                   # "planner_default", "codegen_standard" など
    requirements: LLMSelectionRequirements
    context_stats: ContextStats | None = None
```

profile 名の定義は
`master__selfdevagent_llm_routing_v1.md` に従う。

---

## 4. 出力仕様（Selection Result）

```python
@dataclass
class LLMSelectionResult:
    model_id: str                  # 例: "deepseek-coder"
    reason: str                    # ログ用の説明文
    fallbacks: list[str]           # ["gpt-5.1", "grok-4"]
```

---

## 5. ModelSelector のロジック（v1）

### 5.1 クラスインターフェース

```python
class ModelSelector:
    def __init__(self, model_pool: ModelPool, routing_policy: "RoutingPolicy"):
        self.model_pool = model_pool
        self.policy = routing_policy

    def select(self, request: LLMSelectionRequest) -> LLMSelectionResult:
        """
        profile + requirements + context_stats に基づき、
        最適な model_id と fallback を返す。
        """
        ...
```

### 5.2 RoutingPolicy の役割

```python
class RoutingPolicy:
    """
    プロファイル名から候補モデルセットを作り、
    requirements / context_stats に基づき優先順位をつける。
    """
    def __init__(self, model_pool: ModelPool):
        self.model_pool = model_pool

    def candidate_models_for_profile(self, profile: str) -> list[ModelConfig]:
        ...

    def rank_candidates(
        self,
        candidates: list[ModelConfig],
        requirements: LLMSelectionRequirements,
        context: ContextStats | None,
    ) -> list[ModelConfig]:
        ...
```

---

## 6. プロファイル別の候補セット

`candidate_models_for_profile(profile)` は、
`master__selfdevagent_llm_routing_v1.md` の内容を反映する。

### 6.1 例: planner_default

```python
def candidate_models_for_profile(self, profile: str) -> list[ModelConfig]:
    if profile == "planner_default":
        # model_pool から id を取ってくるイメージ
        ids = ["gpt-5.1", "claude-3.7-sonnet"]
    elif profile == "codegen_standard":
        ids = ["deepseek-coder", "gpt-5.1", "grok-4"]
    elif profile == "codegen_high_risk":
        ids = ["gpt-5.1", "claude-3.7-sonnet", "minimax-m2-reap-162b-a10b"]
    elif profile == "review_multijudge":
        ids = ["gpt-5.1", "claude-3.7-sonnet", "grok-4"]
    elif profile == "docgen_master":
        ids = ["gpt-5.1", "claude-3.7-sonnet"]
    else:
        # fallback: roles や status から推測してもよい
        ids = []

    return [self.model_pool.get(i) for i in ids if self.model_pool.get(i)]
```

---

## 7. ランキングロジック（rank_candidates）

ざっくり v1 のルール:

1. **context_window チェック**

   * `approx_input_tokens + approx_output_tokens` が context_window を超えるものは除外

2. **roles / task_kind 一致**

   * model.roles に requirements.task_kind が含まれていなければスコア下げ or 除外

3. **status 優先**

   * `primary > secondary > experimental`

4. **cost / latency チューニング**

   * cost_sensitivity = "low" → cost_tier="low" を優先
   * latency_sensitivity = "high" → latency_tier="low" を優先

5. **experimental 制御**

   * allow_experimental=False → status="experimental" は除外
   * high risk + allow_experimental=True のときのみ advisor候補として残す

疑似コード:

```python
def rank_candidates(self, candidates, req, ctx):
    scored: list[tuple[float, ModelConfig]] = []

    total_tokens = (ctx.approx_input_tokens + ctx.approx_output_tokens) if ctx else None

    for m in candidates:
        score = 0.0

        # 1. context_window
        if total_tokens and total_tokens > m.context_window:
            continue  # 不適合

        # 2. role 適合
        if req.task_kind in m.roles:
            score += 10.0
        else:
            score -= 5.0

        # 3. status
        if m.status == "primary":
            score += 5.0
        elif m.status == "secondary":
            score += 2.0
        elif m.status == "experimental":
            if not req.allow_experimental:
                continue  # 除外
            score -= 2.0

        # 4. cost
        if req.cost_sensitivity == "low":
            if m.cost_tier == "low":
                score += 3.0
        elif req.cost_sensitivity == "high":
            if m.cost_tier == "high":
                score += 2.0

        # 5. latency
        if req.latency_sensitivity == "high":
            if m.latency_tier == "low":
                score += 3.0

        scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for score, m in scored]
```

---

## 8. LLMRouter

ModelSelector は **「どのモデルを使うか」** を決める。
LLMRouter は **「実際にそのモデルにリクエストを飛ばす」** 役を担う。

### 8.1 インターフェース

```python
class LLMRouter:
    def __init__(self, selector: ModelSelector, clients: dict[str, "LLMClient"]):
        self.selector = selector
        self.clients = clients  # key = provider or model_id

    def complete(self, request: LLMSelectionRequest, prompt: str) -> str:
        selection = self.selector.select(request)
        model_id = selection.model_id

        client = self._client_for_model(model_id)
        try:
            return client.complete(model_id=model_id, prompt=prompt)
        except TransientError:
            # fallback 試行
            for fb_id in selection.fallbacks:
                fb_client = self._client_for_model(fb_id)
                try:
                    return fb_client.complete(model_id=fb_id, prompt=prompt)
                except TransientError:
                    continue
            raise  # 全て失敗

    def _client_for_model(self, model_id: str) -> "LLMClient":
        # 例: model_id → provider からクライアントを選択
        #   "gpt-5.1"      → OpenAIClient
        #   "claude-3.7..."→ AnthropicClient
        #   "grok-4"       → XAIClient
        #   "deepseek-coder"→ DeepSeekClient
        #   "minimax..."   → CerebrasClient / MiniMaxClient
        ...
```

### 8.2 LLMClient Protocol

```python
class LLMClient(Protocol):
    def complete(self, model_id: str, prompt: str) -> str:
        ...
```

将来:

* `chat(messages: list[dict])`
* `tool_calling(...)`
  なども拡張可能。

---

## 9. セーフティ / ログ

* ModelSelector は常に `reason` を返し、
  **「なぜそのモデルが選ばれたか」** をログに残す
* experimental モデルが選択された場合は必ずフラグを付ける
* high_risk タスク（Graph / Template / Security / Infra）は
  `codegen_high_risk` プロファイルで `allow_experimental=True` の場合のみ
  advisor として experimental を使う（直接 codegen には使わない）

ログ例:

```text
[ModelSelector] profile=codegen_standard → model=deepseek-coder
  reason="task_kind=codegen, language=python, primary+low cost"
  fallbacks=["gpt-5.1", "grok-4"]
```

---

## 10. テスト方針

### 10.1 単体テスト

* `test_model_selector.py`

  * プロファイルごとに期待モデルが選ばれるか
  * context_window を超える場合の挙動
  * allow_experimental=False の時に experimental が除外されるか
  * risk_level="high" + allow_experimental=True の時に minimax が候補に含まれるか

* `test_llm_router.py`

  * client が成功したケースで fallback を使わないこと
  * client が TransientError を投げた時に fallback が使われること
  * 全 fallback が失敗した時に例外が上がること

### 10.2 結合テスト（将来）

* SelfDevAgent v4 が profile を指定 →
  実際に特定モデルへルーティングされるかを e2e で確認
* 特定プロファイルで minimax を advisor として使うシナリオ

---

## 11. 今後の拡張

* **動的モデル追加**

  * `master__future_model_pool_v2` に新モデル追加 →
    起動時 or リロードで自動反映
* **オンラインメトリクス連携**

  * 各モデルの成功率 / レイテンシ / コストを記録し、
    RoutingPolicy のスコアリングに反映
* **ユーザー / プロジェクト別ポリシー**

  * 一部プロジェクトで「このモデルは禁止」などの制約を入れる

---

# END

```

---
