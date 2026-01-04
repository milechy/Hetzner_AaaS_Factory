from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from toolgate.audit import AuditEvent, log_audit
from toolgate.evaluator import evaluate
from toolgate.models import EvaluateRequest, EvaluateResponse
from toolgate.policy import PolicyLoadError, PolicyStore


app = FastAPI(title="ToolGate", version="0.1.0")

POLICIES_DIR = Path(os.environ.get("TOOLGATE_POLICIES_DIR", "policies"))
API_KEY = os.environ.get("TOOLGATE_API_KEY")  # optional

store = PolicyStore(policies_dir=POLICIES_DIR)


def _check_auth(authorization: Optional[str]) -> None:
    if not API_KEY:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def post_evaluate(
    req: EvaluateRequest,
    authorization: Optional[str] = Header(default=None),
) -> JSONResponse:
    _check_auth(authorization)

    try:
        policy = store.load(req.policyVersion)
    except PolicyLoadError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = evaluate(policy, req)

    log_audit(
        AuditEvent(
            ts=datetime.now(timezone.utc).isoformat(),
            requestId=req.requestId,
            proposalId=req.proposalId,
            tool=req.tool,
            effect=req.effect,
            decision=result.decision,
            reason=result.reason,
            policyVersion=req.policyVersion,
        )
    )

    resp = EvaluateResponse(
        decision=result.decision, reason=result.reason, policyVersion=req.policyVersion
    )
    return JSONResponse(content=resp.model_dump(mode="json"))