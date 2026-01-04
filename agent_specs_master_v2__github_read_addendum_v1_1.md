# agent_specs_master_v2__github_read_addendum_v1_1.md
AaaS Factory – Agent Specs Addendum (v1.1 GitHub Read)
最終更新: 2025-12-24

---

## 0. 目的
v1.1（GitHub read-only）における Agent 実装要件をSSOT化する。

参照：
- master__tool_unlock_roadmap_v1__addendum_v1_1.md
- master__tool_gate_policy_v1__addendum_v1_1.md

---

## 1. Tool（github_read）利用ルール
- Agent は github_read 実行前に ToolGate evaluate を要求
- allow の場合のみ read を実行
- deny の場合：
  - proposal を継続し、summary に deny 理由を記載（proposal-only維持）

---

## 2. Request の互換拡張（候補）
（v0/v1.0 を破壊しない optional 追加）
- github?: { repo: string, baseBranch?: string }
- githubReadMode?: "off" | "metadata" | "metadata+ci"（default: metadata）

---

## 3. Proposal への反映（スキーマ維持）
- summary に “GitHub Facts” セクションを追加して記載：
  - 重複PRの有無（検知した場合は warning）
  - 直近CIの状態（失敗があれば注意事項）
- manualSteps に以下を追加しうる：
  - 「該当CI失敗の再現確認」
  - 「重複PRがある場合の統合方針確認」

---

## 4. E2E（v1.1）
- シナリオ4：既存PR重複
- シナリオ5：直近CI失敗

---

# END