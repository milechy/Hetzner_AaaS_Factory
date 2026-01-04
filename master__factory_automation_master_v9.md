# Factory Automation Master v9

## 0. 自動化レベル定義（更新）

- L1: Script
- L2: CI
- L3: Agent（Agents SDK）
- L4: Self-Dev（限定的自己進化）

L4 は以下条件下のみ許可：
- 人間承認が入る
- 対象は spec / template / codegen に限定
- infra / security / billing は除外

---

## 1. 自動化の前提

すべての自動化は：
- Agent SDK Agent
- 明示的 Tool
- PR 提案

を満たす必要がある。

---

## 2. LangGraph の位置付け（明文化）

LangGraph は：
- 必須ではない
- Graph 構造が必要な場合のみ採用
- SDK Agent の内側に閉じる

Graph を Factory の SSOT にしない。