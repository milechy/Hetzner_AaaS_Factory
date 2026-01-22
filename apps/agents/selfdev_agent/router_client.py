from __future__ import annotations

from dataclasses import dataclass

from .schemas import Profile, RiskLevel, TaskKind


@dataclass
class RouteDecision:
    selected_model: str
    rationale: str
    fallback_chain: list[str]


class RouterRequiredError(RuntimeError):
    pass


class LLMRouterClient:
    """
    MVP stub. Enforces:
    - routing MUST be used
    - profile is mandatory (writer|reviewer)
    """
    def route(self, *, profile: Profile, risk_level: RiskLevel, task_kind: TaskKind) -> RouteDecision:
        if profile not in ("writer", "reviewer"):
            raise RouterRequiredError("router: invalid or missing profile")
        if profile == "writer":
            return RouteDecision(selected_model="codex", rationale="writer profile", fallback_chain=["codex"])
        return RouteDecision(selected_model="opus-4.5", rationale="reviewer profile", fallback_chain=["opus-4.5"])
