# master__tool_unlock_roadmap_v1__addendum_v1_1.md
AaaS Factory – Tool Unlock Roadmap (v1) Addendum (v1.1 GitHub Read)
最終更新: 2025-12-24

---

## 0. 目的
v1.1 における GitHub read-only 解禁の範囲と、Agent 側の取り込み方針をSSOT化する。

参照：
- master__tool_unlock_roadmap_v1.md
- master__tool_unlock_roadmap_v1__detailed_v1_0.md

---

## 1. v1.1 の目的
v1.0 の sandbox/validate に加え、GitHub 側の “事実（read-only）” を取り込み、
- 既存PRとの重複
- 直近CI失敗の兆候
- 競合リスク
を提案（summary/manualSteps）に反映して品質を上げる。

---

## 2. v1.1 で解禁する Tool（read-only）
- github_read（effect=read）

許容スコープ（read-only）：
- PR 一覧/詳細、PRのファイル一覧
- CI status / check runs
- Issue/labels/milestones（任意）

禁止：
- PR create / merge / comment / label 変更（write は v1.2+）
- secret 取得・ログ出力

---

## 3. Agent の取り込み要件
- GitHub facts は提案の “補足根拠” として summary に短く記載（スキーマ維持）
- 重複PR検知：summary に warning を明記（提案は継続）
- 直近CI失敗：summary に注意事項、manualSteps に再現確認を追加
- existingTree 未提供時：
  - GitHub read から近似 tree を構築可能（精度は落ちる）
  - ただし推奨は existingTree を引き続き提供

---

## 4. v1.1 E2E（最小シナリオ）
- シナリオ4：既存PRと重複
- シナリオ5：直近CI失敗

（詳細は agent_specs / e2e シナリオSSOTに委譲）

---

# END