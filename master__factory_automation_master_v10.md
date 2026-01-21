# Factory Automation Master v10 (Updated)
# SSOT – Evidence-based automation status for the Factory

## 0. Automation Levels (Factual)

- L1: Script (Implemented)
- L2: CI / Release automation (Implemented)
- L3: Agent (Partially Implemented)
- L4: Self-Dev (Not yet implemented as an autonomous loop; policy + prerequisites are implemented)

| Level | Description                          | Implementation Status |
|------:|--------------------------------------|-----------------------|
| L1    | Script                               | Implemented           |
| L2    | CI / Release Factory                  | Implemented           |
| L3    | Agent (PR-first via controlled tools) | Partially Implemented |
| L4    | Self-Dev (Plan→Exec→Review→Reflect)   | Not Implemented       |

Notes:
- “Implemented” means: present in repo, runnable, and governed by SSOT/contract rules.
- “Partially Implemented” means: some agents/tooling exist, but the end-to-end loop is not yet complete.

---

## 1. Current Implementation Status (Evidence-Based)

### 1.1 Implemented (Confirmed in repo)
- **Release Factory (L2)**: GitHub Actions-driven release workflow exists and is the operational truth.
- **Open-PR Contract / ToolGate boundary**: write operations are constrained to the controlled Open-PR flow (PR-first / Human Gate).
- **RepoLock (fail-fast)**: repo-level lock exists as a write-side concurrency guard for OpenPR execution.
- **PRScheduler (fail-fast)**: blocks concurrent Factory PR creation on the same base branch (exit=2 blocked).
- **Work Queue v1 (SSOT-based)**:
  - enqueue SSOT IO (append-only JSONL)
  - transition SSOT (head-of-queue only; invariant enforcement; fail-fast)
- **Model-role policy (SSOT)**:
  - Codex = Writer
  - Opus 4.5 = Reviewer (read-only)
  - enforced as normative policy + routing profile requirements

### 1.2 Partially Implemented
- **L3 Agent layer**:
  - AgentBuilderAgent exists as a concrete agent capability
  - Supporting “controlled tools” exist for PR creation / labeling / locks / scheduling
  - However, the unified SelfDevAgent v4 loop is not yet implemented

### 1.3 Not Implemented / Next-phase Items
- **ContextPackage materialization (AaaS unit context isolation)**
- **Parallel AaaS development orchestration** (multi-workstream execution beyond the Work Queue invariants)
- **Runner separation (Mac / Hetzner)** as a first-class orchestrated capability
- **End-to-end SelfDevAgent v4 execution loop** (Plan→Exec→Review→Reflect) as runnable code
- **High-risk gate automation** beyond policy (i.e., code-level enforcement hooks integrated into the agent runtime)

---

## 2. What This Factory Is Today (Factual)

This Factory is currently:
- A **Release Factory (CI-driven)**
- An **Open-PR Factory (PR-first / Human Gate / controlled write boundary)**
- A **Work Queue v1 Factory (SSOT queue with invariant enforcement)**

This Factory is **not yet**:
- A “parallel AaaS factory” that can run multiple AaaS developments concurrently end-to-end with context isolation and runner orchestration.

---

## 3. Entry Conditions for Semi-Automated Factory Development (Current State)

### 3.1 Prerequisites (now satisfied)
The following prerequisites for semi-automated Factory self-development are **implemented**:
- RepoLock
- Minimal PR scheduling (PRScheduler)
- Mandatory Task Brief (process requirement; codified by SSOT policy)
- PR-first / Human Gate enforced via controlled Open-PR boundary

### 3.2 Current enabling SSOT (authoritative)
- `master__agent_execution_model_policy_v1.md`
- `master__selfdevagent_llm_routing_v3.md`
- `master__tooling_adoption_registry_v1.md` (v1.5)

### 3.3 Next minimal step (v1.x continuation)
Implement **SelfDevAgent v4 MVP** as “proposal-only”:
- Plan (read-only) → Exec (Codex writer) → Verify → Review (Opus read-only) → PR Proposal payload
- No direct push; PR creation remains via controlled OpenPR toolchain with human approval

---

## 4. Scope Guard (Hard)

- LangGraph remains **optional** and MUST NOT become SSOT or control-plane authority.
- Any claim of “implemented” must be backed by repo artifacts (code/workflow/tests/SSOT docs).
- Parallel AaaS development is not declared “implemented” until:
  - ContextPackage exists
  - Work Queue can safely schedule multiple independent workstreams
  - Runner separation is integrated (Hetzner/Mac) with deterministic controls

# END