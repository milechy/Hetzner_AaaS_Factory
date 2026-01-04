# x402 Billing Option Specification v1  
AaaS Factory — Optional Internet-Native Payment Protocol  
最終更新: 2025-11-19

---

# 0. 目的

本仕様書は、AaaS Factory の “将来オプション” として保持する  
**x402 Payment Protocol** の技術定義である。

Factory v1 ではデフォルト採用しないが、  
Agent-to-Agent / Usage-based / API Billing における  
**次世代決済方式**として評価用途で保管する。

---

# 1. x402 とは何か（簡易定義）

- HTTP 402 (Payment Required) を復権させた決済プロトコル  
- クライアント（人間・AI・サービス）が API を呼ぶ →  
  サーバが “402 Payment Required” を返す →  
  支払い URI / 請求情報を x402 形式で返す  
- 支払い後の request では 200/201 が返却される  
- 支払い手段はステーブルコイン等（USDC）  
- Agent-to-Agent、サービス間決済を自然に行える

---

# 2. AaaS Factory での Position（位置づけ）

```

必須: ❌
標準: ❌
オプション: ✔
推奨: ❌

```

理由：

- 現行の Stripe Billing が業界標準  
- x402 はエコシステムが未成熟  
- 通貨・法律・税の管理が SaaS側で必要  
- Factory の “OSS × self-host × low-dependency” とは逆方向  

ただし：

- AIエージェント経済圏  
- micro-payments  
- APIの使用量課金  
- auto-payment loops  
- Web3 SaaS の特殊需要  

という未来要求には強い。

---

# 3. x402 を採用したい SaaS の例

- APIベースの“usage billing”サービス  
- LLM inference API（トークン払い）  
- Agent-to-Agent サービス（LLM同士の自動決済）  
- decentralized services（web3-infrastructure SaaS）

---

# 4. Factory Integration（構造）

Factory で x402 を利用する場合は：

### 4.1 Billing Template 補完

```

/billing/x402/spec/
/billing/x402/handlers/
/billing/x402/examples/
/billing/x402/openapi/

```

### 4.2 必要となる拡張

- DB: トランザクションログ  
- Webhook: payment-confirmation  
- API: payment-intent / payment-consume  
- UI: “Paywall → Payment → Resource”  
- Cron: expired payment cleanup

### 4.3 SpecSyncAgent の対応

SpecSyncAgent は要件から：

```

billing: "x402"

```

を読み取り、Billing Template を注入する。

---

# 5. セキュリティ方針

- ステーブルコインは明示的リスクがある  
- KYC, AML 準拠要（Factory標準では扱わない）  
- 実稼働では “optional” のみで提供  
- Factory 自体は fiat / tax system を扱わない

---

# 6. 現時点の Factory の結論

- v1 の標準は Stripe  
- x402 は **実験的 / オプション的** 扱い  
- SpecSyncAgent / RepoBuilderAgent は “必要時のみ挿入”  
- TemplateAgent は Billing Template の一部として管理  
- 未来の AI 経済圏に向けて “知識として保持” する

---

# END
```

---