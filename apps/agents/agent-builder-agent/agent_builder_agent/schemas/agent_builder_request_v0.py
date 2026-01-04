from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TargetV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repoKind: Literal["monorepo", "single"]
    language: Literal["typescript", "python", "swift"]
    framework: Literal["nextjs", "fastapi", "swiftui", "agents-sdk"]
    runtime: Literal["node20", "python311", "swift59"] = "python311"


class ConstraintsV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    highRiskDomains: list[Literal["infra", "security", "billing", "template"]] = Field(
        default_factory=lambda: ["infra", "security", "billing", "template"]
    )
    disallowNetwork: bool = True
    proposalOnly: Literal[True] = True


class RepoContextV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseBranch: str = "main"
    existingTree: list[str] = Field(default_factory=list)


class AgentBuilderRequestV0(BaseModel):
    """
    v0 contract: specText or specObject is required.
    NOTE: spec content must at least provide name/purpose; steps can be inferred.
    """

    model_config = ConfigDict(extra="forbid")

    requestId: str = Field(min_length=8, max_length=128)
    specFormat: Literal["yaml", "json", "auto"]
    specText: Optional[str] = Field(default=None, min_length=1)
    specObject: Optional[dict[str, Any]] = None

    target: TargetV0
    routingProfile: Literal[
        "planner_standard", "codegen_standard", "reviewer_standard", "docgen_standard"
    ] = "codegen_standard"

    constraints: ConstraintsV0 = Field(default_factory=ConstraintsV0)
    repoContext: RepoContextV0 = Field(default_factory=RepoContextV0)

    def get_spec_payload(self) -> tuple[Optional[str], Optional[dict[str, Any]]]:
        return self.specText, self.specObject

    @classmethod
    def validate_presence_of_spec(cls, values: "AgentBuilderRequestV0") -> "AgentBuilderRequestV0":
        if not values.specText and not values.specObject:
            raise ValueError("Either specText or specObject is required.")
        return values