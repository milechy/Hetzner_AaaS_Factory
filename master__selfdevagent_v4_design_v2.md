# SelfDevAgent v4 Design v2

## 0. 実行基盤

SelfDevAgent は **OpenAI Agents SDK 上で動作**する。

---

## 1. 責務

- SSOT を読み取る
- 改善余地を検出する
- PR 提案を生成する

SelfDevAgent は **実装を直接変更しない**。

---

## 2. 実行ループ

1. Context Build
2. Plan
3. Execute（Tool 呼び出し）
4. Review（自己レビュー）
5. Human Approval
6. Reflect（Memory 更新）

---

## 3. LangGraph との関係

- LangGraph は必須ではない
- 分岐・並列が必要なときのみ使用
- graph.py を SSOT としない