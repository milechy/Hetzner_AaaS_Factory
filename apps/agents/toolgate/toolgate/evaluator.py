from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from toolgate.models import EvaluateRequest, EvaluateResponse, PolicyDoc


@dataclass(frozen=True)
class EvalResult:
    decision: str  # allow/deny
    reason: str


def _norm_path(p: str) -> str:
    return p.replace("\\", "/").lstrip("/").strip()


def _blocked_by_prefixes(paths: list[str], prefixes: list[str]) -> Optional[str]:
    npaths = [_norm_path(p) for p in paths if isinstance(p, str)]
    nprefixes = [_norm_path(x) for x in prefixes if isinstance(x, str)]
    for p in npaths:
        for pref in nprefixes:
            if pref and p.startswith(pref):
                return f"blocked: path '{p}' matches prefix '{pref}'"
    return None


def _allowed_when(rule_allowed: dict[str, Any], req: EvaluateRequest) -> tuple[bool, str]:
    """
    Implements permissive matching:
    - If a constraint exists, req must match it.
    - If it does not exist, it is ignored.
    """
    ctx = req.context

    # humanApproved
    if "humanApproved" in rule_allowed:
        allowed_values = rule_allowed["humanApproved"]
        if isinstance(allowed_values, list):
            if ctx.humanApproved not in allowed_values:
                return False, "humanApproved not satisfied"
        elif isinstance(allowed_values, bool):
            if ctx.humanApproved != allowed_values:
                return False, "humanApproved not satisfied"

    # riskLevel
    if "riskLevel" in rule_allowed:
        allowed_values = rule_allowed["riskLevel"]
        if isinstance(allowed_values, list) and ctx.riskLevel not in allowed_values:
            return False, "riskLevel not satisfied"

    # highRiskDetected
    if "highRiskDetected" in rule_allowed:
        allowed_values = rule_allowed["highRiskDetected"]
        if isinstance(allowed_values, list):
            if ctx.highRiskDetected not in allowed_values:
                return False, "highRiskDetected not satisfied"
        elif isinstance(allowed_values, bool):
            if ctx.highRiskDetected != allowed_values:
                return False, "highRiskDetected not satisfied"

    # maxFilesTouched
    if "maxFilesTouched" in rule_allowed:
        m = rule_allowed["maxFilesTouched"]
        if isinstance(m, int) and ctx.filesTouchedCount > m:
            return False, "maxFilesTouched exceeded"

    # allowedDomains (optional)
    if "allowedDomains" in rule_allowed:
        allowed = rule_allowed["allowedDomains"]
        if isinstance(allowed, list):
            # require at least one overlap if domains are provided
            if ctx.domains and not any(d in allowed for d in ctx.domains):
                return False, "allowedDomains not satisfied"

    return True, "allowedWhen satisfied"


def evaluate(policy: PolicyDoc, req: EvaluateRequest) -> EvalResult:
    # 1) blockedWhen first
    blocked = policy.blockedWhen or {}
    prefixes = []
    if isinstance(blocked.get("pathsPrefix"), list):
        prefixes = blocked["pathsPrefix"]
    why = _blocked_by_prefixes(req.context.pathsTouched, prefixes)
    if why:
        return EvalResult(decision="deny", reason=why)

    # 2) find tool rule matching (tool + effect)
    for rule in policy.tools:
        if rule.tool == req.tool and rule.effect == req.effect:
            ok, reason = _allowed_when(rule.allowedWhen, req)
            if ok:
                return EvalResult(decision="allow", reason=reason)
            return EvalResult(decision="deny", reason=reason)

    # 3) default deny
    return EvalResult(decision="deny", reason="default-deny: no matching rule")