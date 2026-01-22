from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

RiskLevel = Literal["low", "medium", "high"]
TaskKind = Literal["implement", "test_fix", "review", "ssot_update"]
Profile = Literal["writer", "reviewer"]


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
        }
