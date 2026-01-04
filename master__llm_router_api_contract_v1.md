# LLM Router API Contract v1
ファイル名: master__llm_router_api_contract_v1.md
最終更新: 2025-12-24

---

## 0. 原則
- Agent/SDK は model を直接選択しない
- **必ず LLMRouter を経由**
- Agent が指定できるのは **profile** のみ
- high-risk（infra/security/billing/template）を low-cost model に割り当てることは禁止（Router責務）

---

## 1. Endpoint
### 1.1 Complete
- Method: POST
- Path: /v1/complete
- Content-Type: application/json
- Auth: 任意（Bearer Token 推奨）

---

## 2. Request Schema（概略）
```json
{
  "profile": "codegen_standard",
  "input": "string",
  "context": { "task": "infer_steps" }
}

	•	profile: string（必須）
	•	input: string（必須）
	•	context: object（任意、監査/ルーティング補助）

注意：
	•	modelId / provider 指定は禁止（受け取らない）

---

## 3. Response Schema（概略）
{
  "text": "string",
  "meta": {
    "routingProfile": "codegen_standard",
    "riskTier": "low|high",
    "latencyMs": 1234
  }
}

	•	text: string（必須、空は禁止）
	•	meta: object（任意）
	•	Router 内部情報。Agent側は “profile の確認” 程度に留める。

---

## 4. Error
	•	HTTP 4xx/5xx を返す
	•	body は JSON 推奨：
{ "error": { "code": "ROUTER_ERROR", "message": "..." } }

---

END