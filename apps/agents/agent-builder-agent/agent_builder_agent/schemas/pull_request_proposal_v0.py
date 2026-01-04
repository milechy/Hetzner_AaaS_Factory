from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RiskV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["low", "medium", "high"]
    highRiskDetected: bool
    notes: list[str] = Field(default_factory=list, max_length=20)


class ProposedFileV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    action: Literal["create", "modify", "delete"]
    content: str
    contentType: Literal["text", "json", "yaml", "python", "typescript", "swift", "md"] = "text"


class DependencyV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ecosystem: Literal["npm", "pip", "swiftpm"]
    name: str
    requestedVersion: str
    reason: Optional[str] = None


class ChangesV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    directories: list[str] = Field(default_factory=list)
    files: list[ProposedFileV0] = Field(default_factory=list, min_length=1)
    dependencies: list[DependencyV0] = Field(default_factory=list)


class CheckV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["lint", "test", "build", "typecheck"]
    command: str
    cwd: Optional[str] = None


class ValidationV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checks: list[CheckV0] = Field(default_factory=list)
    manualSteps: list[str] = Field(default_factory=list)


class MetadataV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routerProfile: str
    modelAgnostic: Literal[True] = True
    createdAt: datetime


class PullRequestProposalV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposalId: str = Field(min_length=8, max_length=128)
    requestId: str = Field(min_length=8, max_length=128)

    title: str = Field(min_length=5, max_length=120)
    summary: str = Field(min_length=20, max_length=4000)

    risk: RiskV0
    changes: ChangesV0
    validation: ValidationV0
    metadata: MetadataV0