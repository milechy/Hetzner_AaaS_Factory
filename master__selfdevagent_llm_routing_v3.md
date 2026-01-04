# SelfDevAgent LLM Routing v3

## 0. 原則

- Agent SDK は LLM を直接選ばない
- **必ず LLMRouter を経由**

---

## 1. 呼び出し位置

Agent → Router → Model

Agent は profile のみ指定可能。

---

## 2. High-Risk 分離

以下は禁止：
- infra / security / billing を low-cost model に割り当てる

Router は risk-aware 判定を行う。