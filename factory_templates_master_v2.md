# factory_templates_master_v2.md
AaaS Factory – Templates Master (v2)  
最終更新: 2025-12-24

---

# 🎯 目的（Purpose）

本ファイルは AaaS Factory の  
**SaaS / AaaS / Agent プロジェクトを自動生成するための  
テンプレート群の唯一の真理（SSOT）** である。

v2 では従来の SaaS テンプレ（Web / API / Infra / CI）に加え、  
**Agent プロジェクト（proposal-only / Router-first）** を  
Factory の第一級テンプレとして正式に統合する。

---

# 🧩 0. Template Philosophy（思想）

1. **テンプレは常に “最低限 + 拡張可能”**  
2. **テンプレの修正はすべて PR / Proposal ベース**  
3. **テンプレにない要素は SaaS / Agent 側に直接書かず、テンプレに昇格させる**  
4. **Factory の経験を蓄積して標準化し続ける**  
5. **Agent は判断、実行は Tool / Human に委ねる**（v2 追加）

---

# 🗂 1. テンプレートのレイヤー構成（v2）

v2 ではテンプレを **5レイヤー** で定義する：

1. **App Templates**  
   - Next.js / API / SwiftUI

2. **Infra Templates**  
   - Docker / Coolify / Terraform

3. **CI/CD Templates**  
   - GitHub Actions / Runner

4. **Metadata Templates**  
   - README / API Spec / Design Spec

5. **Agent Templates（v2 追加）**  
   - proposal-only Agent
   - Router-first / model-agnostic

---

# 🗂 2. Factory 標準ディレクトリ構造

templates/
├─ nextjs/
├─ api/
├─ swiftui/
├─ infra/
├─ cicd/
└─ agents/              # v2 追加（Agent Templates）

---

# 🌐 3. Next.js Template（Web App）

（※ v1 内容をそのまま継承）

### stack
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn/ui or DS-based UI Kit
- SWR
- Zod

### base layout.tsx（例）
```tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-surface-root text-text-primary">
        {children}
      </body>
    </html>
  );
}


⸻

🛠 4. Backend API Template

（※ v1 内容をそのまま継承）
	•	FastAPI or Node.js
	•	Prisma
	•	OpenAPI 準拠

⸻

📱 5. SwiftUI Template

（※ v1 内容をそのまま継承）
	•	SwiftUI
	•	MVVM
	•	Async API Client

⸻

🧱 6. Infra Templates

（※ v1 内容をそのまま継承）
	•	Docker / docker-compose
	•	Coolify
	•	Terraform（Hetzner）

※ v2 以降も infra 直接生成は Agent v0 では禁止

⸻

🔁 7. CI/CD Templates

（※ v1 内容をそのまま継承）
	•	GitHub Actions
	•	self-hosted runner（Linux / macOS）

⸻

🤖 8. Agent Templates（v2 追加・重要）

Factory v2 は Agent プロジェクトを正式に扱う。

Agent テンプレは 「実装する」のではなく
「変更を提案する」 ことを第一目的とする。

⸻

8.1 AgentBuilderAgent v0（proposal-only）

概要
	•	Spec（YAML / JSON）を入力
	•	skeleton（ディレクトリ / ファイル草案）を生成
	•	PullRequestProposal(JSON) を出力
	•	ここで停止（git / PR / merge は行わない）

制約（必須）
	•	git write / push / merge を行わない
	•	infra change / secret 操作を行わない
	•	LLM は 必ず LLMRouter 経由
	•	Agent が指定できるのは profile のみ
	•	high-risk（infra / security / billing / template）は
	•	検出は行う
	•	skeleton は生成してよい
	•	ファイル生成は行わない

標準テンプレ（SSOT）
	•	参照:
factory_templates_master_v2__agent_builder_agent_v0.md

⸻

8.2 Agent Templates の配置

apps/
└─ agents/
   └─ agent-builder-agent/

単体リポ構成でも可。

⸻

8.3 入出力 Schema（必須 SSOT）

AgentBuilderAgent v0 の入出力は
以下の Schema を唯一の真理とする：
	•	schemas__agent_builder_request_v0.json
	•	schemas__pull_request_proposal_v0.json
	•	schemas__agent_builder_error_v0.json

⸻

8.4 LLM Router 契約（必須参照）

Agent Templates は LLM Router API Contract を前提とする。
	•	参照:
master__llm_router_api_contract_v1.md

原則：
	•	model ID の直指定禁止
	•	profile のみ指定
	•	Router が model / cost / risk を制御

⸻

🧪 9. Agent / Proposal 向け CI（v2）

proposal-only プロジェクト向けに
最小 CI を定義する。
	•	ruff
	•	pytest
	•	typecheck（必要に応じて）

※ apply / merge / deploy は禁止
	•	参照:
cicd_master_v2__proposal_validation_addendum.md

⸻

🧠 10. TemplateAgent のルール（v2）
	1.	テンプレ修正は常に PR / Proposal で行う
	2.	SaaS / Agent の改善はテンプレへ昇格させる
	3.	本マスター（v2）が常に最優先 SSOT
	4.	Agent は判断のみ、実行は Tool / Human に委ねる
	5.	high-risk は常に明示・段階的に解放する

⸻

🔮 11. 将来拡張（v3 以降）
	•	AgentBuilderAgent v1（Tool 解禁）
	•	Diff / CI 自動実行 Agent
	•	High-risk 段階解放ポリシー
	•	Multi-Agent orchestration templates
	•	Agent-driven SaaS factory

⸻

END