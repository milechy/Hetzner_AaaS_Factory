from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

RiskLevel = Literal["low", "medium", "high"]
TaskKind = Literal["implement", "test_fix", "review", "ssot_update"]
Profile = Literal["writer", "reviewer"]
InvariantSeverity = Literal["warn", "fix_required"]
InvariantCode = Literal[
    "INV_ROUTER_PROOFS_MISSING",
    "INV_ROUTER_PROOF_WRITER_MISSING",
    "INV_ROUTER_PROOF_REVIEWER_MISSING",
    "INV_ROUTER_PROOF_FIELDS_INVALID",
    "INV_ROUTER_PROOF_REVIEW_TASK_KIND_INVALID",
    "INV_PLAN_MISSING",
    "INV_PLAN_STEPS_EMPTY",
    "INV_PLAN_STEP_EMPTY",
    "INV_CONTEXT_SCAN_MISSING",
    "INV_CONTEXT_TASK_ID_MISMATCH",
    "INV_CONTEXT_GOAL_EMPTY",
    "INV_RISK_LEVEL_MISMATCH",
]


@dataclass
class TaskBrief:
    task_id: str
    goal: str
    non_goals: List[str] = field(default_factory=list)
    repo_scope: List[str] = field(default_factory=list)
    risk_hint: Optional[RiskLevel] = None
    definition_of_done: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class FileChangeSummary:
    path: str
    summary: str


@dataclass
class ContextIntentScan:
    task_id: str
    goal: str
    non_goals: List[str] = field(default_factory=list)
    repo_scope: List[str] = field(default_factory=list)
    risk_hint: Optional[RiskLevel] = None
    definition_of_done: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "non_goals": self.non_goals,
            "repo_scope": self.repo_scope,
            "risk_hint": self.risk_hint,
            "definition_of_done": self.definition_of_done,
            "constraints": self.constraints,
        }


@dataclass
class PlanStep:
    step: str
    status: str = "planned"

    def to_dict(self) -> Dict[str, Any]:
        return {"step": self.step, "status": self.status}


@dataclass
class Plan:
    steps: List[PlanStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": [step.to_dict() for step in self.steps]}


@dataclass
class ReflectionNote:
    note: str

    def to_dict(self) -> Dict[str, Any]:
        return {"note": self.note}


@dataclass
class RouterDecisionProof:
    profile: Profile
    risk_level: RiskLevel
    task_kind: TaskKind
    selected_model: str
    rationale: str
    fallback_chain: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile,
            "risk_level": self.risk_level,
            "task_kind": self.task_kind,
            "selected_model": self.selected_model,
            "rationale": self.rationale,
            "fallback_chain": list(self.fallback_chain),
        }


@dataclass
class InvariantFinding:
    code: InvariantCode
    severity: InvariantSeverity
    message: str
    field: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "field": self.field,
        }


@dataclass
class ProposalValidation:
    invariants_ok: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fix_required_questions: List[str] = field(default_factory=list)
    checked_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invariants_ok": self.invariants_ok,
            "violations": list(self.violations),
            "warnings": list(self.warnings),
            "fix_required_questions": list(self.fix_required_questions),
            "checked_items": list(self.checked_items),
        }


@dataclass
class PRProposal:
    summary: str
    risk_level: RiskLevel
    task_kind: TaskKind
    files_changed: List[FileChangeSummary] = field(default_factory=list)
    verification: Dict[str, Any] = field(default_factory=dict)
    review_notes: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    context_scan: Optional[ContextIntentScan] = None
    plan: Optional[Plan] = None
    reflection: List[ReflectionNote] = field(default_factory=list)
    router_proofs: List[RouterDecisionProof] = field(default_factory=list)
    invariant_findings: List[InvariantFinding] = field(default_factory=list)
    validation: Optional[ProposalValidation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "risk_level": self.risk_level,
            "task_kind": self.task_kind,
            "files_changed": [fc.__dict__ for fc in self.files_changed],
            "verification": self.verification,
            "review_notes": self.review_notes,
            "open_questions": self.open_questions,
            "context_scan": self.context_scan.to_dict() if self.context_scan else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "reflection": [note.to_dict() for note in self.reflection],
            "router_proofs": [proof.to_dict() for proof in self.router_proofs],
            "invariant_findings": [finding.to_dict() for finding in self.invariant_findings],
            "validation": self.validation.to_dict() if self.validation else None,
        }
