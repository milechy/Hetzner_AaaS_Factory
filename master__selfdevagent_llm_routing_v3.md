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

---

## PRProposal.router_proofs (RouterDecisionProof) — SSOT

### Purpose
SelfDevAgent v4 の proposal-only 出力 `PRProposal.router_proofs` は、
**「どの profile が、どの条件で、どのモデルを選んだか」**を機械検証できる形で残す。
人間レビュー／CI／後続エージェントが、**ルーティング逸脱**を検知するための根拠とする。

### Data Contract (required)
`router_proofs[]` の各要素（RouterDecisionProof）は以下を必須とする:

- `profile`
- `risk_level`
- `task_kind`
- `selected_model`
- `rationale`
- `fallback_chain`

### Invariants (validation rules)
以下は **Hard**（逸脱は failure 扱い）:

1) **proposal-only boundary**
- `router_proofs` は「ルーティングの証跡」であり、PR作成や git 操作の権限を与えない。
- proposal payload に含めるだけで、外部副作用は持たない。

2) **Minimum proofs**
- `router_proofs` は **最低2件**を含む（writer → reviewer の順）。
  - 1件目: profile=`writer`
  - 2件目: profile=`reviewer`

3) **Profile ↔ Model mapping**
- profile=`writer` の `selected_model` は **Codex 系**でなければならない。
- profile=`reviewer` の `selected_model` は **Opus 4.5**でなければならない。
（具体名は Implementation が持ってよいが、SSOT として “writer≠reviewer” は固定）

4) **Task-kind consistency**
- reviewer proof の `task_kind` は **必ず** `review`。
- writer proof の `task_kind` は実タスク種別（例: implement / ssot_update）を反映する。

5) **Traceability**
- rationale は空文字禁止。
- fallback_chain は空配列禁止。selected_model を含むこと。

### Consumer guidance
CI / Review agent は以下を自動チェックできる:
- proofs 件数（>=2）
- writer/reviewer の順序
- profile と model の整合性
- fallback_chain の健全性（空でない・selected_model を含む）

# END
