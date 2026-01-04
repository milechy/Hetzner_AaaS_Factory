from __future__ import annotations

from agent_builder_agent.schemas.agent_builder_error_v0 import AgentBuilderErrorV0


def error_response(*, request_id: str, code: str, message: str, details: list[str] | None = None) -> dict:
    err = AgentBuilderErrorV0(
        requestId=request_id,
        errorCode=code,  # validated by pydantic Literal
        message=message,
        details=details or [],
    )
    return err.model_dump(mode="json")