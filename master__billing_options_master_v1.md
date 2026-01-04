# Billing Options Master v1  
AaaS Factory — Payment & Billing Architecture  
最終更新: 2025-11-19

---

# 0. 目的

本ドキュメントは AaaS Factory が自動生成する SaaS が利用する  
**決済 / 課金 / 請求の選択肢**を統一的に管理するための  
Single Source of Truth (SSOT) である。

AaaS Factory は “Factory 自体が自己改善する” という設計思想のため、  
課金方法もプラガブルかつテンプレベースで管理できるようにする。

---

# 1. 現行標準（v1 Standard）

## 1.1 Stripe Billing（デフォルト）
- SaaS の標準課金方式  
- Checkout Session / Billing Portal / Webhook  
- SaaS リポ生成時に Billing SDK が自動注入される  
- Subscription / Usage-based どちらも対応  
- 法務・税制度との整合性が高い  
- AaaS Factory v1 の正式採用方式

## 1.2 Manual Billing（小規模 SaaS）
- 完全従量課金にならない PoC / クローズドベータ導入用  
- “Admin creates invoices manually” モード  
- Factory の internal SaaS にのみ使用

---

# 2. 将来オプション（Future Options）

以下は “v2 以降のオプション候補” として保持し、  
SpecSyncAgent が要件に応じて推薦する。

## 2.1 x402 Payment Protocol（Internet-native Payment）【NEW】
- HTTP 402（Payment Required）を復活させたインターネット課金プロトコル  
- Agent-to-Agent / Service-to-Service 決済に強い  
- ステーブルコイン（USDCなど）による即時決済  
- クリエイターエコノミー、API課金、AI Agent課金に向く  
- 現時点では採用しないが、将来に向けて “適用候補” として保持

## 2.2 Crypto-based Billing（Wallet Sign-in）
- Web3 SaaS のための “wallet login + billing”  
- x402 以外のチェーン決済方式  
- 現在は Options として保持（採用なし）

## 2.3 External Enterprise Billing Systems
- Chargebee  
- Recurly  
- KillBill  
- Zuora  
→ 現状では非推奨。必要な SaaS が現れるまで “保留”。

---

# 3. Billing Template Architecture

Factory が SaaS 生成時に注入する Billing Template は：

```

/billing/
stripe/
api/
components/
webhooks/
x402/  (optional)
spec/
handlers/
manual/
admin/

```

x402 は “optional モジュール” として存在し、  
SpecSyncAgent / RepoBuilderAgent が要件に応じて注入する。

---

# 4. エージェント連携

- **SpecSyncAgent**  
  → 要件から決済方式を推定（stripe / x402 / manual）  
- **RepoBuilderAgent**  
  → 選ばれた Billing Template を SaaS リポに注入  
- **UIDesignAgent**  
  → Checkout / PaymentFlow の UI を生成  
- **TemplateAgent**  
  → Billing 全体のテンプレ更新管理  
- **GraphEditorAgent**  
  → Billing workflows を graph に追加（x402の場合も同様）

---

# 5. 今後のロードマップ（v2, v3）

- Usage-based billing（細粒度メーター計測）  
- Agent-to-Agent micropayment（x402連携）  
- hybrid billing（stripe + microtoken）  
- in-factory billing visualizer  
- custom BillingAgent を導入し、課金の drift を監視

---

# END
```

---