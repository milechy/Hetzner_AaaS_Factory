# Agent Roles Master v3

2024-06-21

## 0. Agent / Tool 分離原則

- Agent = 判断・計画・提案のみ
- Tool = 実行（副作用あり）

Agent が以下を直接行うことは禁止：
- git write
- infra change
- secret 操作
- billing 操作
- template 昇格操作

---

## 1. Tool 最小化ルール

- 新規 Tool はデフォルトで P2 とし、SSOT の更新が必須
- Tool は単一責任であり、明示的に監査可能であること

---

## 2. 標準 Tool（Core）

- read
- test
- git_diff
- pr_proposal
- ci_check

すべて Tool 経由。

---

## 3. High-Risk Tool の扱い

High-Risk Tool の定義、及び運用ルールは master__security_checklist にて管理し、ここに重複して記述しないこと。

---

## 4. 人間向け補助ツール（非中核）

- lazygit などの人間専用補助ツールは存在してよいが、PR/SSOT ルールを迂回してはならない。

---

# Factory Master v3

2024-06-21

## 3. Tool 設計原則

### 3.1 Tool は最小化する（Tool Minimization）

- Tool は最小限かつ単一責任であること
- 監査可能であること
- 追加は必ず SSOT の更新を伴うこと

### 3.2 標準抽象を優先する（Standard Abstractions First）

- GitHub PR、CI チェック、workflow、diff ベースの提案を優先する

### 3.3 万能 shell 実行ツールは禁止

- 便利であっても汎用的な bash/OS 実行ツールは明示的に禁止する

---

## 4. 禁止事項

（既存内容をそのまま保持）