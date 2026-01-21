# SelfDevAgent LLM Routing v3
# SSOT – Profiles: Writer (Codex) / Reviewer (Opus 4.5)

## 0. 原則（Hard）

- Agent SDK は LLM を直接選ばない
- **必ず LLMRouter を経由**
- ルーティングは **profile + risk + task_kind** で決める
- profile は **Writer / Reviewer** の2つのみ（v3）

---

## 1. 呼び出し位置

Agent → Router → Model

Agent は次のみ指定可能:
- `profile`: writer | reviewer
- `risk_level`: low | medium | high
- `task_kind`: implement | test_fix | review | ssot_update

---

## 2. プロファイル定義（Hard）

### 2.1 writer = Codex（実装専任）
- 目的: 実装、修正、テスト→修正ループ、PR提案作成
- 許可: workspace write / run_* / open_pr_create（approval_token必須）
- 禁止: ToolGate/approval回避、直接push、禁止パス変更

### 2.2 reviewer = Opus 4.5（レビュー専任・read-only）
- 目的: 差分レビュー、規約逸脱検出、SSOT衝突検出
- 許可: read-only tools のみ
- 禁止: workspace write / run_* / open_pr_create など write-side effect

---

## 3. High-Risk 分離（Hard）

以下は禁止：
- infra / security / billing / contract / lock / queue を low-cost model に割り当てる
- high-risk で reviewer を省略する

Router は risk-aware 判定を行う。

High-risk の追加ルール:
- `risk_level=high` の場合、PR作成前に必ず reviewer（Opus 4.5）のレビューを通す
- open_pr_create の approval_scope に high-risk 対象が含まれていなければ FAIL

---

## 4. ルーティング規約（Normative defaults）

- implement / test_fix → profile=writer → Codex
- review / ssot_conflict_check → profile=reviewer → Opus 4.5
- ssot_update（軽微）→ reviewer先行 → writer（Codex）で反映案作成
- ssot_update（high-risk）→ reviewer必須 + human gate（approval_scope明示）

---

## 5. 出力要件（Router I/O）

Router は必ず以下を返す:
- selected_model
- profile
- risk_level
- cost_tier
- rationale (short, machine-readable)
- fallback_chain (optional)

Agent は selected_model をログに残し、ツール呼び出し時に `profile` を必ず付与する。

# END