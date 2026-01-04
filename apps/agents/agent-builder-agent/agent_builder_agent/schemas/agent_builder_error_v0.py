from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentBuilderErrorV0(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requestId: str = Field(min_length=8, max_length=128)
    errorCode: Literal[
        "SPEC_PARSE_FAILED",
        "SPEC_VALIDATION_FAILED",
        "HIGH_RISK_BLOCKED",
        "UNSUPPORTED_TARGET",
        "INTERNAL_ERROR",
    ]
    message: str
    details: list[str] = Field(default_factory=list, max_length=50)