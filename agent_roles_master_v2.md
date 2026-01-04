# Agent Roles Master v2

## 0. Agent / Tool 分離原則

- Agent = 判断・計画
- Tool = 実行

Agent が以下を直接行うことは禁止：
- git write
- infra change
- secret 操作

---

## 1. 標準 Tool

- read
- test
- git_diff
- pr_proposal
- ci_check

すべて Tool 経由。