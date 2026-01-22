from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .router_client import LLMRouterClient
from .schemas import (
    ContextIntentScan,
    Plan,
    PlanStep,
    PRProposal,
    ReflectionNote,
    RiskLevel,
    TaskBrief,
    TaskKind,
)


class PermissionDeniedError(RuntimeError):
    pass


@dataclass
class ToolPermissions:
    profile: str  # "writer" | "reviewer"

    def assert_can_write(self) -> None:
        if self.profile != "writer":
            raise PermissionDeniedError("permission: reviewer is read-only (write denied)")

    def assert_can_run(self) -> None:
        if self.profile != "writer":
            raise PermissionDeniedError("permission: reviewer is read-only (run denied)")


class SelfDevAgentV4:
    """
    MVP: proposal-only loop.
    Plan (read-only) -> Exec (writer) -> Verify -> Review (reviewer) -> PRProposal payload.
    """
    def __init__(self, router: LLMRouterClient) -> None:
        self.router = router

    def plan(self, brief: TaskBrief) -> tuple[RiskLevel, TaskKind, List[str]]:
        _ = self.router.route(profile="reviewer", risk_level=brief.risk_hint or "low", task_kind="review")
        risk: RiskLevel = brief.risk_hint or "low"
        kind: TaskKind = "implement"
        steps = [
            "Inspect repo scope and relevant files (read-only).",
            "Draft minimal change plan and safety notes.",
        ]
        return risk, kind, steps

    def scan_context_intent(self, brief: TaskBrief) -> ContextIntentScan:
        return ContextIntentScan(
            task_id=brief.task_id,
            goal=brief.goal,
            non_goals=list(brief.non_goals),
            repo_scope=list(brief.repo_scope),
            risk_hint=brief.risk_hint,
            definition_of_done=list(brief.definition_of_done),
            constraints=list(brief.constraints),
        )

    def planner(self, brief: TaskBrief) -> Plan:
        _ = brief
        return Plan(
            steps=[
                PlanStep(step="Confirm task brief intent and scope."),
                PlanStep(step="Sketch minimal change set and verify boundaries."),
            ]
        )

    def exec(self, brief: TaskBrief, risk: RiskLevel, kind: TaskKind) -> List[str]:
        _ = self.router.route(profile="writer", risk_level=risk, task_kind=kind)
        perms = ToolPermissions(profile="writer")
        perms.assert_can_write()
        return ["(MVP) exec stub: would apply code changes under OpenPR boundary."]

    def verify(self, risk: RiskLevel, kind: TaskKind) -> dict:
        _ = self.router.route(profile="writer", risk_level=risk, task_kind="test_fix")
        perms = ToolPermissions(profile="writer")
        perms.assert_can_run()
        return {"tests": {"status": "not_run", "notes": "MVP stub"}, "lint": {"status": "not_run"}}

    def review(self, brief: TaskBrief, risk: RiskLevel, kind: TaskKind) -> List[str]:
        _ = self.router.route(profile="reviewer", risk_level=risk, task_kind="review")
        perms = ToolPermissions(profile="reviewer")
        # Assert reviewer cannot write:
        try:
            perms.assert_can_write()
            raise AssertionError("reviewer write should have been denied")
        except PermissionDeniedError:
            pass
        return ["(MVP) review stub: reviewer read-only notes."]

    def reflect(
        self,
        brief: TaskBrief,
        risk: RiskLevel,
        kind: TaskKind,
        review_notes: List[str],
    ) -> List[ReflectionNote]:
        _ = brief, risk, kind
        return [ReflectionNote(note=f"(MVP) reflection stub: {len(review_notes)} review note(s).")]

    def run(self, brief: TaskBrief) -> PRProposal:
        context_scan = self.scan_context_intent(brief)
        plan = self.planner(brief)
        risk, kind, _steps = self.plan(brief)
        _ = self.exec(brief, risk, kind)
        verification = self.verify(risk, kind)
        review_notes = self.review(brief, risk, kind)
        reflection = self.reflect(brief, risk, kind, review_notes)

        return PRProposal(
            summary=f"SelfDevAgent v4 MVP proposal for task_id={brief.task_id}",
            risk_level=risk,
            task_kind=kind,
            verification=verification,
            review_notes=review_notes,
            context_scan=context_scan,
            plan=plan,
            reflection=reflection,
        )
