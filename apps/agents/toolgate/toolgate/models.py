from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


Decision = Literal["allow", "deny"]
Effect = Literal["read", "validate", "write"]


class ToolGateContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    humanApproved: bool = False
    riskLevel: Literal["low", "medium", "high"] = "low"
    highRiskDetected: bool = False

    pathsTouched: list[str] = Field(default_factory=list)
    filesTouchedCount: int = 0
    domains: list[str] = Field(default_factory=list)


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policyVersion: str = Field(min_length=1, max_length=128)
    requestId: str = Field(min_length=1, max_length=256)
    proposalId: Optional[str] = Field(default=None, max_length=256)

    tool: str = Field(min_length=1, max_length=128)
    effect: Effect
    context: ToolGateContext


class EvaluateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    reason: str
    policyVersion: str


class PolicyToolRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str
    effect: Effect
    allowedWhen: dict[str, Any] = Field(default_factory=dict)


class PolicyDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    blockedWhen: dict[str, Any] = Field(default_factory=dict)
    tools: list[PolicyToolRule] = Field(default_factory=list)