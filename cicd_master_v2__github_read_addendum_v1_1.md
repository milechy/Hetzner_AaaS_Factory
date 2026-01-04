# cicd_master_v2__github_read_addendum_v1_1.md
CI/CD Master v2 Addendum – GitHub Read Observability (v1.1)
最終更新: 2025-12-24

---

## 0. 目的
v1.1 の github_read（read-only）導入により、提案の品質と失敗回避を高める観測性要件をSSOT化する。

---

## 1. CI観点の取り込み（read-only）
- 直近の check runs / status を取得して summary に反映
- 失敗がある場合、manualSteps に「再現確認」を入れることを推奨

---

## 2. 禁止事項
- github_read で取得した情報から secret を抽出・ログ出力しない
- write 操作（PR作成/コメント/ラベル付け）は v1.1 では行わない

---

# END