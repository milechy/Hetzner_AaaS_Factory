# Tooling & Knowledge Adoption Registry v1.2
# SSOT – Authoritative Record of Evaluated Tools, OSS, and Concepts

## Binding Rule (Hard)

- This registry is the **single source of truth** for all tooling / model / external service adoption decisions.
- If a tool / service / model is NOT listed here, it MUST be treated as **not adopted** by default.
- GPT agents MUST NOT propose, assume, or use any tool not explicitly marked as Adopted or Conditional here.
- Rationale and constraints in this registry override any implicit assumptions from other documents.

## 0.1 Change Log
- v1.1: Add normative metadata fields (Reference SSOT, Revisit Condition, AdoptedAt) and proposal gate rules to prevent re‑proposal drift.
- v1.2: Adopt `requests` (Supporting) for RepoLock GitHub REST calls (limited scope).

## 0. Purpose

This document is the **single source of truth** for all external tools, open‑source projects, services, and technical concepts that have been proposed during the development of the AaaS Factory.

Rules:
- If a tool/idea is not listed here, it MUST NOT be proposed or introduced.
- Status definitions are binding across all chats, agents, and implementations.
- “Not Adopted” does not mean low quality; it means **out of scope for current Factory versions**.
- Any proposal of tools/URLs/models **MUST** be registered here first; items not present here **MUST NOT** be suggested or implemented.

---

## 1. Adopted (Core or Supporting)

### Core Platform & Control
- OpenAI Agents SDK  
  Status: Adopted (Core)  
  Scope: Agent execution, tool control, PR-first workflows  
  Notes: Central execution substrate for Factory agents

### Development & Execution
- VS Code Agent Mode / GitHub Copilot Agent Mode  
  Status: Adopted  
  Scope: Execution layer only (no autonomous decisions)

- Name: requests (Python HTTP client)
  Status: Adopted (Supporting)
  Scope: `tools/repo_lock.py` GitHub REST API calls (GET/POST/DELETE) for RepoLock acquire/release only.
  Prohibited: General-purpose external HTTP access (scraping, arbitrary third-party API integration, unattended runtime network expansion).
  Rationale: RepoLock requires GitHub `git/refs` operations; `requests` is the minimal dependency to perform authenticated REST calls and classify 403 PAT-insufficient failures deterministically.
  Reference SSOT: `factory_master_v3.md`, `master__factory_automation_master_v10.md`, `master__security_checklist_v2.md`
  AdoptedAt: 2026-01-13
  Revisit Condition: Replace RepoLock HTTP implementation with Python stdlib (urllib) and remove the runtime dependency.

### Infrastructure & Ops
- Postgres PITR  
  Status: Adopted  
  Scope: Infra reliability and recovery  
  Reference: infra_runbook_postgres_pitr_v1.md

### Model Strategy
- Multi-model routing (LLMRouter v2)  
  Status: Adopted  
  Scope: Cost-aware, risk-aware routing  
  References: llm_router_design_v1.md, master__future_model_pool_v1.md

---

## 2. Conditionally Adopted / Limited Scope

### Visualization / Prototyping
- LangFlow  
  Status: Conditionally Adopted  
  Scope: Prototyping / visualization only  
  Prohibited: Production control plane, SSOT replacement

### Graph Orchestration
- LangGraph  
  Status: Conditionally Adopted  
  Scope: Optional execution graphs  
  Prohibited: Central authority, implicit state

### Mobile / Browser Automation
- mobile-mcp  
  Status: Conditionally Adopted (High-Risk)  
  Scope: Experimental only  
  Prohibited: Default tooling, unattended execution

### Models
- MiniMax M2  
  Status: Conditionally Adopted  
  Scope: Future model pool only  
  Reference: master__future_model_pool_v1.md

---

## 3. Explicitly Not Adopted (Current Versions)

### Agent Frameworks / Autonomous Systems
- AutoAgent
- AgentScope
- Devin
- Trae
- Continue
- Sweep
- OpenHands
- HackGPT
- Mini-Agent
- HopX
- AgentMark
- OpenCode
- DeepCode

Reason: Conflicts with PR-first, human-gated, SSOT-controlled Factory model.

### Memory / Context Layers
- MemOS
- Acontext
- home-rag (runtime use)
- mem-layer
- Memori

Reason: Cross-run state, uncontrolled persistence, violates determinism.

### Security / Offensive Tooling
- PentestAgent
- Vidoc Security
- bypass-bot-detection
- securevibes
- heretic
- wafw00f

Reason: High-risk, non-essential for Factory launch.

### Billing / Payments
- Dodopayments
- KillBill
- x402-agent-demo-app (runtime use)

Reason: Out of scope for Factory bootstrap.

### UI / Design Systems (Factory Core)
- superdesign
- cult-ui
- square-ui
- paceui/saaskit-starter
- heroUI
- Rive
- Pencil
- reactbits

Reason: UI handled in separate UI workflow; not Factory core.

### Misc / Infra / Tools
- Pinokio
- Appwrite
- FreeDomain
- s3fs-fuse (for core state)
- Parcel
- Zed
- Ghostty
- lazygit (automation use)

---

## 4. Deferred / Reference Only (Knowledge, Articles, Ideas)

- Agents 2.0 / Deep Agents (Phil Schmid article)
- Instacart Intent Engine article
- Linux Networking ip command article
- how-to-build-a-coding-agent (ghuntley)
- LLM datasets (mlabonne)
- AI Security awesome lists

Status: Reference-only; no direct implementation allowed.

---

## 5. Change Policy

- Updates require PR and human approval.
- Each change must include:
  - Reason
  - Version impact
  - Link to related SSOT
- CHANGELOG update required for version boundary changes.

## 6. Entry Template (Normative)

All new entries **MUST** use the following fields:

- **Name**:
- **Status**: Adopted | Conditionally Adopted | Not Adopted | Deferred
- **Scope**: (where it is allowed)
- **Prohibited**: (explicit non‑uses)
- **Rationale**: (why this decision was made)
- **Reference SSOT**: (one or more authoritative docs, e.g. `factory_master_v3.md §2.1`)
- **AdoptedAt**: YYYY‑MM‑DD
- **Revisit Condition**: (clear, testable condition or `Never`)

Entries missing these fields are considered **invalid**.

Enforcement: GPT/Agents **MUST** treat this registry as the final authority. Re‑proposing items marked Not Adopted or outside their allowed Scope is a policy violation.

# END