from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .router_client import LLMRouterClient, RouteDecision
from .schemas import (
    ContextIntentScan,
    Plan,
    PlanStep,
    PRProposal,
    ReflectionNote,
    RouterDecisionProof,
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

    def exec(self, brief: TaskBrief, risk: RiskLevel, kind: TaskKind) -> tuple[List[str], RouteDecision]:
        route_decision = self.router.route(profile="writer", risk_level=risk, task_kind=kind)
        perms = ToolPermissions(profile="writer")
        perms.assert_can_write()
        return ["(MVP) exec stub: would apply code changes under OpenPR boundary."], route_decision

    def verify(self, risk: RiskLevel, kind: TaskKind) -> dict:
        _ = self.router.route(profile="writer", risk_level=risk, task_kind="test_fix")
        perms = ToolPermissions(profile="writer")
        perms.assert_can_run()
        return {
            "tests": {"status": "not_run", "command": "pytest"},
            "lint": {"status": "not_run", "command": "ruff check ."},
            "format": {"status": "not_run", "command": "ruff format ."},
        }

    def review(
        self,
        brief: TaskBrief,
        risk: RiskLevel,
        kind: TaskKind,
        exec_decision: RouteDecision,
    ) -> tuple[List[str], RouteDecision, List[RouterDecisionProof], List[str]]:
        route_decision = self.router.route(profile="reviewer", risk_level=risk, task_kind="review")
        perms = ToolPermissions(profile="reviewer")
        # Assert reviewer cannot write:
        try:
            perms.assert_can_write()
            raise AssertionError("reviewer write should have been denied")
        except PermissionDeniedError:
            pass
        router_proofs = [
            RouterDecisionProof(
                profile="writer",
                risk_level=risk,
                task_kind=kind,
                selected_model=exec_decision.selected_model,
                rationale=exec_decision.rationale,
                fallback_chain=exec_decision.fallback_chain,
            ),
            RouterDecisionProof(
                profile="reviewer",
                risk_level=risk,
                task_kind="review",
                selected_model=route_decision.selected_model,
                rationale=route_decision.rationale,
                fallback_chain=route_decision.fallback_chain,
            ),
        ]
        review_notes: List[str] = []
        open_questions: List[str] = []
        if not isinstance(router_proofs, list):
            review_notes.append("FAIL: router_proofs must be a list")
            open_questions.append("Is router_proofs a list with at least two entries?")
        else:
            review_notes.append("PASS: router_proofs is a list")
            if len(router_proofs) >= 2:
                review_notes.append("PASS: router_proofs has at least two entries")
            else:
                review_notes.append("FAIL: router_proofs has fewer than two entries")
                open_questions.append("Why does router_proofs contain fewer than two entries?")
            for idx, proof in enumerate(router_proofs):
                payload = proof.to_dict() if hasattr(proof, "to_dict") else proof.__dict__
                missing = [key for key in ("profile", "selected_model") if key not in payload]
                if missing:
                    review_notes.append(
                        f"FAIL: router_proofs[{idx}] missing keys: {', '.join(missing)}"
                    )
                    open_questions.append(
                        f"Is router_proofs[{idx}] missing required keys (profile, selected_model)?"
                    )
                else:
                    review_notes.append(f"PASS: router_proofs[{idx}] has required keys")
                profile = payload.get("profile")
                if profile in {"writer", "reviewer"}:
                    review_notes.append(f"PASS: router_proofs[{idx}] profile is valid")
                else:
                    review_notes.append(f"FAIL: router_proofs[{idx}] profile is invalid")
                    open_questions.append(
                        f"Is router_proofs[{idx}] profile limited to writer or reviewer?"
                    )
        return review_notes, route_decision, router_proofs, open_questions

    def reflect(
        self,
        brief: TaskBrief,
        risk: RiskLevel,
        kind: TaskKind,
        review_notes: List[str],
        open_questions: List[str],
    ) -> List[ReflectionNote]:
        _ = brief, risk, kind
        total_notes = len(review_notes)
        fail_notes = sum(1 for note in review_notes if note.startswith("FAIL"))
        if total_notes:
            review_summary = f"Review findings: {total_notes} note(s), {fail_notes} fail(s)."
        else:
            review_summary = "Review findings: no notes recorded."
        notes = [ReflectionNote(note=review_summary)]
        if fail_notes:
            next_step = "Next step: address failing review checks and re-validate router_proofs."
        elif open_questions:
            next_step = "Next step: answer open questions and align plan vs review outcomes."
        else:
            next_step = "Next step: align plan vs review outcomes and prep follow-up actions."
        notes.append(ReflectionNote(note=next_step))
        if open_questions:
            notes.append(
                ReflectionNote(
                    note=f"Open questions: {len(open_questions)} item(s) need resolution."
                )
            )
        return notes

    def run(self, brief: TaskBrief) -> PRProposal:
        context_scan = self.scan_context_intent(brief)
        plan = self.planner(brief)
        risk, kind, _steps = self.plan(brief)
        _, exec_decision = self.exec(brief, risk, kind)
        verification = self.verify(risk, kind)
        review_notes, review_decision, router_proofs, open_questions = self.review(
            brief, risk, kind, exec_decision
        )
        reflection = self.reflect(brief, risk, kind, review_notes, open_questions)

        return PRProposal(
            summary=f"SelfDevAgent v4 MVP proposal for task_id={brief.task_id}",
            risk_level=risk,
            task_kind=kind,
            verification=verification,
            review_notes=review_notes,
            open_questions=open_questions,
            context_scan=context_scan,
            plan=plan,
            reflection=reflection,
            router_proofs=router_proofs,
        )
