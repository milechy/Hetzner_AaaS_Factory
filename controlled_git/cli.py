from __future__ import annotations
import argparse, json, os, uuid, re
from datetime import datetime, timedelta, timezone
import hmac, hashlib
import urllib.request
import urllib.error
from typing import Any

def _stable_json_dumps(obj) -> str:
  return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def _read_json(path: str) -> dict:
  with open(path, "r", encoding="utf-8") as f:
    return json.load(f)

def _write_json(obj: dict, path: str | None) -> None:
  s = json.dumps(obj, ensure_ascii=False, indent=2)
  if path:
    with open(path, "w", encoding="utf-8") as f:
      f.write(s)
  else:
    print(s)

def _audit(event: str, data: dict) -> None:
  """Append-only JSONL audit log (best-effort)."""
  path = os.environ.get("AUDIT_LOG_PATH", "")
  if not path:
    return
  rec = {
    "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "event": event,
    "data": data,
  }
  try:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
      f.write(_stable_json_dumps(rec) + "\n")
  except Exception:
    # best-effort: never break execution due to audit logging
    pass

def _match_globs(path: str, globs: list[str]) -> bool:
  import fnmatch
  return any(fnmatch.fnmatch(path, g) for g in globs)

def _rule_matches(rule: dict, path: str) -> bool:
  match = rule.get("match", {})
  any_globs = match.get("pathGlobAny", [])
  none_globs = match.get("pathGlobNone", [])
  if any_globs and not _match_globs(path, any_globs):
    return False
  if none_globs and _match_globs(path, none_globs):
    return False
  return True

def canonical_proposal_hash(proposal: dict) -> str:
  minimal = {
    "metadata": {
      "repo": proposal["metadata"]["repo"],
      "baseBranch": proposal["metadata"]["baseBranch"],
      "proposalId": proposal["metadata"]["proposalId"],
      "title": proposal["metadata"].get("title", ""),
    },
    "changes": {
      "files": [{"path": f["path"], "patch": f.get("patch","")} for f in proposal.get("changes", {}).get("files", [])]
    },
  }
  raw = _stable_json_dumps(minimal).encode("utf-8")
  return "sha256:" + hashlib.sha256(raw).hexdigest()

def policy_check(proposal: dict, policy_path: str) -> dict:
  policy = _read_json(policy_path)
  files = proposal.get("changes", {}).get("files", [])
  rules = policy.get("rules", [])
  unmatched_behavior = policy.get("aggregation", {}).get("unmatchedFilesAre", "reject")

  rejected, allowed = [], []
  notes = []
  domains = set()
  blocked = []

  for f in files:
    path = f["path"]
    matched = None
    for r in rules:
      if _rule_matches(r, path):
        matched = r
        break
    if matched is None:
      if unmatched_behavior == "reject":
        rejected.append(path)
        notes.append(f"{path}: UNMATCHED reject (no allow rule matched)")
      else:
        allowed.append(path)
        notes.append(f"{path}: UNMATCHED allow")
      continue

    rid = matched.get("id", "UNKNOWN_RULE")
    decision = matched.get("decision")
    reason = matched.get("reason", "")
    domain = matched.get("domain")

    if decision == "reject":
      rejected.append(path)
      blocked.append(path)
      notes.append(f"{path}: {rid} reject ({reason})")
      if domain:
        domains.add(domain)
    else:
      allowed.append(path)
      notes.append(f"{path}: {rid} allow ({reason})")

  allowed_overall = (len(rejected) == 0 and len(files) > 0)
  h = canonical_proposal_hash(proposal)

  return {
    "repo": proposal["metadata"]["repo"],
    "baseBranch": proposal["metadata"]["baseBranch"],
    "decision": {
      "allowed": allowed_overall,
      "reason": "allowlist-only; reject_if_any_reject",
      "risk": {
        "highRiskDetected": (len(domains) > 0),
        "domains": sorted(list(domains)),
        "notes": notes,
        "blockedFiles": blocked,
      },
      "allowedFiles": allowed if allowed_overall else [],
      "rejectedFiles": rejected,
    },
    "normalizedProposalHash": h,
    "warnings": [],
  }

def sign(payload: dict, secret: str) -> str:
  msg = _stable_json_dumps(payload).encode("utf-8")
  sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
  return "hmac-sha256:" + sig

def _parse_iso_z(dt: str) -> datetime:
  # Accept ISO-8601 with optional 'Z'
  if dt.endswith("Z"):
    dt = dt[:-1] + "+00:00"
  return datetime.fromisoformat(dt)


def verify_token(token: dict, secret: str) -> tuple[bool, str]:
  """Verify signature and expiry. Returns (ok, reason)."""
  sig = token.get("signature", "")
  if not sig.startswith("hmac-sha256:"):
    return (False, "missing_or_invalid_signature")

  payload = dict(token)
  payload.pop("signature", None)
  exp_sig = sign(payload, secret)
  if not hmac.compare_digest(sig, exp_sig):
    return (False, "signature_mismatch")

  scope = (token.get("scope") or {})
  exp = scope.get("expiresAt")
  if not exp:
    return (False, "missing_expiresAt")
  try:
    exp_dt = _parse_iso_z(exp)
  except Exception:
    return (False, "invalid_expiresAt")
  if datetime.now(timezone.utc) > exp_dt:
    return (False, "expired")

  return (True, "ok")


def _require_scope(token: dict, repo: str, base: str, action: str, actor: str | None = None) -> None:
  scope = (token.get("scope") or {})
  if scope.get("repo") != repo:
    raise SystemExit("token scope repo mismatch")
  if scope.get("baseBranch") != base:
    raise SystemExit("token scope baseBranch mismatch")
  actions = scope.get("actions") or []
  if action not in actions:
    raise SystemExit(f"token scope missing action: {action}")
  if actor is not None:
    tok_actor = scope.get("actorId")
    # actorId is strongly required in v1.2. Treat missing/mismatch as 403-equivalent (deny).
    if not tok_actor:
      raise SystemExit("deny(403): token scope missing actorId (v1.2 requires actorId)")
    if tok_actor != actor:
      raise SystemExit("deny(403): token scope actorId mismatch")

def _gh_request(method: str, url: str, token: str, payload: dict | None = None, timeout: int = 30) -> tuple[int, str]:
  headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "controlled-git-v1.2",
  }
  data = None
  if payload is not None:
    body = json.dumps(payload).encode("utf-8")
    headers["Content-Type"] = "application/json"
    data = body

  req = urllib.request.Request(url, data=data, headers=headers, method=method)
  try:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
      return resp.status, resp.read().decode("utf-8")
  except urllib.error.HTTPError as e:
    try:
      txt = e.read().decode("utf-8")
    except Exception:
      txt = str(e)
    return e.code, txt
  except Exception as e:
    return 0, str(e)


# Helper to classify 403s (PAT/org policy/permission limitations). This is best-effort.
# NOTE: Fallback itself should not depend on this heuristic; the heuristic only refines the reason.
def _classify_403(body: str) -> str:
  b = (body or "").lower()
  if "resource not accessible" in b:
    return "pat_403"
  if "insufficient permissions" in b:
    return "insufficient_permissions"
  if "must have admin rights" in b:
    return "admin_required"
  if "requires authentication" in b:
    return "requires_auth"
  if "forbidden" in b:
    return "forbidden"
  return "gh_403"

def main() -> None:
  ap = argparse.ArgumentParser(prog="cg")
  sub = ap.add_subparsers(dest="cmd", required=True)

  pcheck = sub.add_parser("policy-check")
  pcheck.add_argument("--proposal", required=True)
  pcheck.add_argument("--policy", default="config/policy/controlled_git_policy_v1_2.json")
  pcheck.add_argument("--out")

  approve = sub.add_parser("approve")
  approve.add_argument("--approval-request", required=True)
  approve.add_argument("--actor", required=True)
  approve.add_argument("--minutes", type=int, default=240)
  approve.add_argument("--out")

  vtok = sub.add_parser("verify-token")
  vtok.add_argument("--token", required=True)

  opr = sub.add_parser("open-pr")
  opr.add_argument("--proposal", required=True)
  opr.add_argument("--approval-token", required=True)
  opr.add_argument("--actor")
  opr.add_argument("--out")

  args = ap.parse_args()

  if args.cmd == "policy-check":
    proposal = _read_json(args.proposal)
    res = policy_check(proposal, args.policy)
    _write_json(res, args.out)
    return

  if args.cmd == "approve":
    secret = os.environ.get("APPROVAL_HMAC_SECRET", "")
    if not secret:
      raise SystemExit("APPROVAL_HMAC_SECRET is required")
    req = _read_json(args.approval_request)

    # accept either plain policy-check output or wrapped request
    repo = req.get("repo") or req.get("metadata", {}).get("repo") or req.get("proposal", {}).get("repo")
    base = req.get("baseBranch") or req.get("metadata", {}).get("baseBranch") or req.get("proposal", {}).get("baseBranch")
    ph = req.get("normalizedProposalHash") or req.get("proposal", {}).get("normalizedProposalHash")
    if not (repo and base and ph):
      raise SystemExit("approval-request must include repo, baseBranch, normalizedProposalHash")

    exp = (datetime.now(timezone.utc) + timedelta(minutes=args.minutes)).replace(microsecond=0).isoformat()
    token = {
      "id": str(uuid.uuid4()),
      "issuedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
      "issuedBy": "human",
      "scope": {"repo": repo, "baseBranch": base, "proposalHash": ph, "expiresAt": exp, "actions": ["prepare_branch","apply_patch","open_pr"], "actorId": args.actor},
    }
    token["signature"] = sign(token, secret)
    _write_json(token, args.out)
    return

  if args.cmd == "verify-token":
    secret = os.environ.get("APPROVAL_HMAC_SECRET", "")
    if not secret:
      raise SystemExit("APPROVAL_HMAC_SECRET is required")
    tok = _read_json(args.token)
    ok, reason = verify_token(tok, secret)
    _write_json({"ok": ok, "reason": reason, "scope": tok.get("scope", {})}, None)
    return

  if args.cmd == "open-pr":
    # v1.2: open PR if possible; otherwise return fallback URL on PAT-limited 403
    secret = os.environ.get("APPROVAL_HMAC_SECRET", "")
    if not secret:
      raise SystemExit("APPROVAL_HMAC_SECRET is required")

    gh_token = os.environ.get("GITHUB_TOKEN", "")
    if not gh_token:
      raise SystemExit("GITHUB_TOKEN is required")

    proposal = _read_json(args.proposal)
    approval = _read_json(args.approval_token)

    ok, reason = verify_token(approval, secret)
    if not ok:
      _audit("PR_OPEN_DENIED", {"reason": reason, "repo": proposal.get("metadata", {}).get("repo"), "base": proposal.get("metadata", {}).get("baseBranch")})
      raise SystemExit(f"approval token invalid: {reason}")

    repo = proposal["metadata"]["repo"]
    base = proposal["metadata"]["baseBranch"]

    actor = (args.actor or os.environ.get("CG_ACTOR") or os.environ.get("GITHUB_ACTOR") or "").strip()
    if not actor:
      raise SystemExit("--actor or CG_ACTOR/GITHUB_ACTOR env is required")

    _require_scope(approval, repo, base, "open_pr", actor=actor)

    head = proposal["metadata"].get("headBranch") or os.environ.get("HEAD_BRANCH")
    if not head:
      raise SystemExit("proposal.metadata.headBranch or HEAD_BRANCH env is required")

    proposal_hash = canonical_proposal_hash(proposal)
    if (approval.get("scope") or {}).get("proposalHash") != proposal_hash:
      raise SystemExit("token scope proposalHash mismatch")

    api = os.environ.get("GITHUB_API_BASE_URL", "https://api.github.com").rstrip("/")
    pr_url = f"{api}/repos/{repo}/pulls"
    title = proposal["metadata"].get("title") or f"Proposal {proposal['metadata'].get('proposalId','') }"
    body = (proposal["metadata"].get("body") or "") + f"\n\nProposalHash: {proposal_hash}\nTokenId: {approval.get('id')}\n"

    status, txt = _gh_request("POST", pr_url, gh_token, {
      "title": title,
      "body": body,
      "head": head,
      "base": base,
    })

    if status in (200, 201):
      pr = json.loads(txt)
      _audit("PR_OPENED", {"repo": repo, "base": base, "head": head, "prUrl": pr.get("html_url"), "prNumber": pr.get("number")})
      _write_json({"status": "opened", "prUrl": pr.get("html_url"), "prNumber": pr.get("number")}, args.out)
      return

    # v1.2 fail-safe fallback:
    # - 401/403 should never strand the user; return a browser PR-create URL.
    # - 403 reason classification is best-effort (recommendation), not a hard dependency.
    if status in (401, 403):
      pr_create_url = f"https://github.com/{repo}/pull/new/{head}?expand=1"
      reason_code = "gh_401" if status == 401 else _classify_403(txt)
      _audit(
        "PR_OPEN_FALLBACK",
        {
          "repo": repo,
          "base": base,
          "head": head,
          "prCreateUrl": pr_create_url,
          "status": status,
          "reason": reason_code,
          "message": (txt or "")[:300],
        },
      )
      _write_json(
        {
          "status": "fallback",
          "prCreateUrl": pr_create_url,
          "reason": reason_code,
          "githubApiBaseUrl": api,
        },
        args.out,
      )
      return

    _audit("PR_OPEN_FAILED", {"repo": repo, "base": base, "head": head, "status": status, "message": (txt or "")[:300]})
    raise SystemExit(f"open-pr failed: status={status} body={(txt or '')[:300]}")

if __name__ == "__main__":
  main()
