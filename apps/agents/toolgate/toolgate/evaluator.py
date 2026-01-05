from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from toolgate.models import EvaluateRequest, EvaluateResponse, PolicyDoc


@dataclass(frozen=True)
class EvalResult:
    decision: str  # allow/deny
    reason: str


def _norm_path(p: str) -> str:
    # v1.3: normalize separators and surrounding whitespace only.
    # Leading "/" is NOT stripped here; absolute-path detection is done in integrity checks.
    return p.replace("\\", "/").strip()


def _validate_paths_touched(paths: list[str]) -> tuple[bool, list[str], str]:
    """
    v1.3 ToolGate Context Integrity
    - Relative paths only (no leading '/')
    - No '..' segments
    - No empty strings
    - Use normalized + unique set for evaluation
    Returns: (ok, unique_normalized_paths, reason_if_not_ok)
    """
    if not isinstance(paths, list):
      return False, [], "context.pathsTouched invalid type (expected list)"

    normalized: list[str] = []
    seen: set[str] = set()

    for raw in paths:
      if not isinstance(raw, str):
        continue
      p = _norm_path(raw)

      if not p:
        return False, [], "context.pathsTouched contains empty path"

      if p.startswith("/"):
        return False, [], f"context.pathsTouched must be relative (got absolute): '{raw}'"

      # forbid any '..' segment
      parts = [x for x in p.split("/") if x != ""]
      if any(seg == ".." for seg in parts):
        return False, [], f"context.pathsTouched contains '..' segment: '{raw}'"

      # re-join to collapse accidental double slashes while preserving content
      p2 = "/".join(parts)

      if p2 not in seen:
        seen.add(p2)
        normalized.append(p2)

    return True, normalized, "ok"


def _context_integrity_check(req: EvaluateRequest) -> tuple[bool, list[str], str]:
    """
    v1.3:
    - Validate pathsTouched
    - Enforce filesTouchedCount consistency against unique(normalize(pathsTouched))
    - Enforce non-empty pathsTouched for write-effect actions
    Returns: (ok, unique_normalized_paths, reason_if_not_ok)
    """
    ctx = req.context
    ok, uniq_paths, why = _validate_paths_touched(ctx.pathsTouched)
    if not ok:
      return False, [], why

    # write-effect boundary: empty pathsTouched is not allowed
    if req.effect == "write" and len(uniq_paths) == 0:
      return False, [], "context.pathsTouched must be non-empty for write-effect"

    # filesTouchedCount consistency (v1.3 recommends denial on mismatch; we enforce denial)
    try:
      declared = int(ctx.filesTouchedCount)
    except Exception:
      return False, [], "context.filesTouchedCount invalid (expected int)"

    if declared != len(uniq_paths):
      return (
        False,
        [],
        f"context integrity violation: filesTouchedCount={declared} but unique(pathsTouched)={len(uniq_paths)}",
      )

    return True, uniq_paths, "ok"


def _blocked_by_prefixes(paths: list[str], prefixes: list[str]) -> Optional[str]:
    # Note: paths are expected to be v1.3-normalized and already validated as relative.
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

    # maxFilesTouched (v1.3: evaluate against normalized unique paths)
    if "maxFilesTouched" in rule_allowed:
        m = rule_allowed["maxFilesTouched"]
        if isinstance(m, int):
            ok, uniq_paths, why = _validate_paths_touched(ctx.pathsTouched)
            if not ok:
                return False, why
            if len(uniq_paths) > m:
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
    # v1.3: context integrity checks (deny on violation)
    ok, uniq_paths, why = _context_integrity_check(req)
    if not ok:
        return EvalResult(decision="deny", reason=why)

    # 1) blockedWhen first
    blocked = policy.blockedWhen or {}
    prefixes = []
    if isinstance(blocked.get("pathsPrefix"), list):
        prefixes = blocked["pathsPrefix"]
    why = _blocked_by_prefixes(uniq_paths, prefixes)
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