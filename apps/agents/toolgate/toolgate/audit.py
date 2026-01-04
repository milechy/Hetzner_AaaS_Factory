from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class AuditEvent:
    ts: str
    requestId: str
    proposalId: Optional[str]
    tool: str
    effect: str
    decision: str
    reason: str
    policyVersion: str


def log_audit(event: AuditEvent) -> None:
    print(json.dumps(asdict(event), ensure_ascii=False))