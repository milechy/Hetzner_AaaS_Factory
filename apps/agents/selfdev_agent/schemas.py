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
class PRProposal:
    summary: str
    risk_level: RiskLevel
    task_kind: TaskKind
    files_changed: List[FileChangeSummary] = field(default_factory=list)
    verification: Dict[str, Any] = field(default_factory=dict)
    review_notes: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "risk_level": self.risk_level,
            "task_kind": self.task_kind,
            "files_changed": [fc.__dict__ for fc in self.files_changed],
            "verification": self.verification,
            "review_notes": self.review_notes,
            "open_questions": self.open_questions,
        }
