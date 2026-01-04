from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from agent_builder_agent.core.risk_detector import RiskResult
from agent_builder_agent.schemas.pull_request_proposal_v0 import (
    ChangesV0,
    CheckV0,
    MetadataV0,
    PullRequestProposalV0,
    ProposedFileV0,
    RiskV0,
    ValidationV0,
)


def _risk_level(r: RiskResult) -> str:
    if r.high_risk_detected:
        return "high"
    return "low"


def build_pull_request_proposal(
    *,
    request_id: str,
    router_profile: str,
    title: str,
    summary: str,
    risk: RiskResult,
    directories: list[str],
    files: list[tuple[str, str, str]],  # (path, contentType, content)
    dependencies: list[dict],
) -> PullRequestProposalV0:
    proposed_files = [
        ProposedFileV0(path=p, action="create", contentType=ct, content=c)
        for (p, ct, c) in files
    ]

    checks = [
        CheckV0(kind="lint", command="python -m ruff check .", cwd="."),
        CheckV0(kind="test", command="pytest", cwd="."),
    ]

    manual = []
    if risk.high_risk_detected:
        manual.append("Human gate required: high-risk signals detected; verify omitted domains are not needed.")

    proposal = PullRequestProposalV0(
        proposalId=f"prp_{uuid4().hex[:16]}",
        requestId=request_id,
        title=title,
        summary=summary,
        risk=RiskV0(level=_risk_level(risk), highRiskDetected=risk.high_risk_detected, notes=risk.notes[:20]),
        changes=ChangesV0(
            directories=directories,
            files=proposed_files,
            dependencies=[],
        ),
        validation=ValidationV0(checks=checks, manualSteps=manual),
        metadata=MetadataV0(routerProfile=router_profile, modelAgnostic=True, createdAt=datetime.now(timezone.utc)),
    )
    return proposal