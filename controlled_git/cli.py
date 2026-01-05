from __future__ import annotations
import argparse, json, os, uuid, re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hmac, hashlib
import urllib.request
import urllib.error

from typing import Any

# SSOT linkage (v1.3)
SSOT_CONTRACT_VERSION = "v1.3"
SSOT_DOCUMENT = "master__open_pr_contract_v1_3.md"

@dataclass
class CGError(Exception):
  code: str
  message: str
  details: dict

  def to_json(self) -> dict:
    return {
      "ok": False,
      "code": self.code,
      "message": self.message,
      "details": self.details,
      "contractVersion": SSOT_CONTRACT_VERSION,
      "ssotDocument": SSOT_DOCUMENT,
    }

def _emit(obj: dict, out_path: str | None) -> None:
  _write_json(obj, out_path)

def _emit_error_json(code: str, message: str, details: dict, out_path: str | None = None) -> None:
  obj = {
    "ok": False,
    "code": code,
    "message": message,
    "details": details,
    "contractVersion": SSOT_CONTRACT_VERSION,
    "ssotDocument": SSOT_DOCUMENT,
  }
  _write_json(obj, out_path)

def _emit_ok_json(status: str, payload: dict, out_path: str | None = None) -> None:
  d = {
    "ok": True,
    "status": status,
    "contractVersion": SSOT_CONTRACT_VERSION,
    "ssotDocument": SSOT_DOCUMENT,
  }
  d.update(payload)
  _write_json(d, out_path)

def _fail(code: str, message: str, **details: Any) -> None:
  raise CGError(code=code, message=message, details=details)

def _parse_bool_env(name: str) -> bool:
  v = (os.environ.get(name, "") or "").strip().lower()
  return v in ("1", "true", "yes", "on")

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

def _load_revocation_ids(path: str) -> set[str]:
  """
  Accept either:
    - JSON array of token ids: ["...","..."]
    - JSON object with ids list: {"revokedIds":[...]}
    - JSONL with one object per line containing {"id":"..."}
  """
  ids: set[str] = set()
  try:
    with open(path, "r", encoding="utf-8") as f:
      raw = f.read()
  except Exception:
    return ids

  s = raw.strip()
  if not s:
    return ids

  # Try JSON first
  try:
    obj = json.loads(s)
    if isinstance(obj, list):
      for x in obj:
        if isinstance(x, str) and x:
          ids.add(x)
    elif isinstance(obj, dict):
      xs = obj.get("revokedIds") or obj.get("ids") or []
      if isinstance(xs, list):
        for x in xs:
          if isinstance(x, str) and x:
            ids.add(x)
    return ids
  except Exception:
    pass

  # Fallback to JSONL
  for line in s.splitlines():
    line = (line or "").strip()
    if not line:
      continue
    try:
      obj = json.loads(line)
      tid = obj.get("id")
      if isinstance(tid, str) and tid:
        ids.add(tid)
    except Exception:
      continue

  return ids


def verify_token(token: dict, secret: str) -> tuple[bool, str]:
  """v1.3: Verify signature, expiry, and optional revocation. Returns (ok, code)."""
  sig = token.get("signature", "")
  if not sig.startswith("hmac-sha256:"):
    return (False, "APPROVAL_INVALID_SIGNATURE")

  payload = dict(token)
  payload.pop("signature", None)
  exp_sig = sign(payload, secret)
  if not hmac.compare_digest(sig, exp_sig):
    return (False, "APPROVAL_INVALID_SIGNATURE")

  scope = (token.get("scope") or {})
  exp = scope.get("expiresAt")
  if not exp:
    return (False, "APPROVAL_EXPIRED")
  try:
    exp_dt = _parse_iso_z(exp)
  except Exception:
    return (False, "APPROVAL_EXPIRED")
  if datetime.now(timezone.utc) > exp_dt:
    return (False, "APPROVAL_EXPIRED")

  # Optional revocation
  rev_path = (os.environ.get("APPROVAL_REVOCATION_LIST_PATH", "") or "").strip()
  if rev_path:
    tid = (token.get("id") or "").strip()
    revoked = _load_revocation_ids(rev_path)
    if tid and tid in revoked:
      return (False, "APPROVAL_REVOKED")

  return (True, "OK")

def _require_scope(token: dict, repo: str, base: str, action: str, actor: str | None = None) -> None:
  scope = (token.get("scope") or {})
  if scope.get("repo") != repo:
    _fail("APPROVAL_SCOPE_MISMATCH", "token scope repo mismatch", expected=repo, got=scope.get("repo"))
  if scope.get("baseBranch") != base:
    _fail("APPROVAL_SCOPE_MISMATCH", "token scope baseBranch mismatch", expected=base, got=scope.get("baseBranch"))

  actions = scope.get("actions") or []
  if action not in actions:
    _fail("APPROVAL_SCOPE_MISMATCH", "token scope missing action", action=action, actions=actions)

  if actor is not None:
    tok_actor = scope.get("actorId")
    # actorId is mandatory-by-default. Treat missing/mismatch as 403-equivalent (deny).
    if not tok_actor:
      _fail("APPROVAL_ACTOR_MISMATCH", "deny(403): token scope missing actorId (v1.3 mandatory-by-default)", actor=actor)
    if tok_actor != actor:
      _fail("APPROVAL_ACTOR_MISMATCH", "deny(403): token scope actorId mismatch", actor=actor, tokenActorId=tok_actor)

def _get_github_api_base_url() -> tuple[str, bool]:
  """
  v1.3: GITHUB_API_BASE_URL is a SHOULD parameter.
  Guard:
    - strip trailing '/'
    - empty/invalid => fallback to https://api.github.com and emit audit warning
  Returns (base_url, used_default).
  """
  raw = (os.environ.get("GITHUB_API_BASE_URL", "") or "").strip()
  default = "https://api.github.com"
  if not raw:
    return (default, True)

  base = raw.rstrip("/")
  # Minimal validation: require https:// and no whitespace
  if (not base.startswith("https://")) or (" " in base) or ("\t" in base) or ("\n" in base):
    _audit("WARN_GITHUB_API_BASE_URL_FALLBACK", {"provided": raw, "fallback": default})
    return (default, True)

  return (base, False)

def _classify_403(body: str) -> dict:
  """
  v1.3: best-effort normalization of 403 responses.
  IMPORTANT: Fail-safe fallback MUST NOT depend on classification success.
  Returns a machine-readable reason object.
  """
  b = (body or "").lower()

  # Common GitHub message for org/repo restrictions on PATs / org policies.
  if "resource not accessible" in b:
    return {"code": "GITHUB_403_PAT_RESOURCE_NOT_ACCESSIBLE", "detail": "resource not accessible by token"}
  if "not accessible by personal access token" in b:
    return {"code": "GITHUB_403_PAT_RESOURCE_NOT_ACCESSIBLE", "detail": "resource not accessible by personal access token"}
  if "organization has enabled oauth app access restrictions" in b:
    return {"code": "GITHUB_403_ORG_POLICY", "detail": "oauth app access restrictions"}
  if "saml" in b and "enforced" in b:
    return {"code": "GITHUB_403_ORG_POLICY", "detail": "saml enforced / authorization required"}
  if "insufficient permissions" in b:
    return {"code": "GITHUB_403_INSUFFICIENT_PERMISSIONS", "detail": "insufficient permissions"}
  if "must have admin rights" in b:
    return {"code": "GITHUB_403_INSUFFICIENT_PERMISSIONS", "detail": "admin rights required"}
  if "requires authentication" in b:
    return {"code": "GITHUB_403_INSUFFICIENT_PERMISSIONS", "detail": "requires authentication"}
  if "forbidden" in b:
    return {"code": "GITHUB_403_INSUFFICIENT_PERMISSIONS", "detail": "forbidden"}

  return {"code": "GITHUB_403_UNKNOWN", "detail": "unclassified 403"}

def _gh_request(method: str, url: str, token: str, payload: dict | None = None, timeout: int = 30) -> tuple[int, str]:
  headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "controlled-git-v1.3",
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


def main() -> None:
  ap = argparse.ArgumentParser(prog="cg")
  sub = ap.add_subparsers(dest="cmd", required=True)

  pcheck = sub.add_parser("policy-check")
  pcheck.add_argument("--proposal", required=True)
  pcheck.add_argument("--policy", default="config/policy/controlled_git_policy_v1_2.json")
  pcheck.add_argument("--out")
  pcheck.add_argument("--json", action="store_true", help="emit machine-readable JSON (v1.3)")

  approve = sub.add_parser("approve")
  approve.add_argument("--approval-request", required=True)
  approve.add_argument("--actor", required=True)
  approve.add_argument("--minutes", type=int, default=240)
  approve.add_argument("--out")
  approve.add_argument("--json", action="store_true", help="emit machine-readable JSON (v1.3)")

  vtok = sub.add_parser("verify-token")
  vtok.add_argument("--token", required=True)
  vtok.add_argument("--out")
  vtok.add_argument("--json", action="store_true", help="emit machine-readable JSON (v1.3)")

  opr = sub.add_parser("open-pr")
  opr.add_argument("--proposal", required=True)
  opr.add_argument("--approval-token", required=True)
  opr.add_argument("--actor")
  opr.add_argument("--out")
  opr.add_argument("--json", action="store_true", help="emit machine-readable JSON (v1.3)")

  ctc = sub.add_parser("contract")
  ctc.add_argument("--json", action="store_true", help="emit machine-readable JSON (v1.3)")

  args = ap.parse_args()

  try:
    if args.cmd == "contract":
      if getattr(args, "json", False):
        _emit_ok_json(
          "contract",
          {
            "code": "OK",
            "contractVersion": SSOT_CONTRACT_VERSION,
            "ssotDocument": SSOT_DOCUMENT,
          },
          None,
        )
      else:
        print(f"contractVersion={SSOT_CONTRACT_VERSION}\nssotDocument={SSOT_DOCUMENT}")
      return

    if args.cmd == "policy-check":
      proposal = _read_json(args.proposal)
      res = policy_check(proposal, args.policy)
      if getattr(args, "json", False):
        # v1.3: standardized envelope. Keep legacy top-level keys for compatibility.
        payload = {"code": "OK"}
        payload.update(res)
        _emit_ok_json("policy_checked", payload, args.out)
      else:
        _write_json(res, args.out)
      return

    if args.cmd == "approve":
      secret = os.environ.get("APPROVAL_HMAC_SECRET", "")
      if not secret:
        _fail("APPROVAL_HMAC_SECRET_REQUIRED", "APPROVAL_HMAC_SECRET is required")
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
      # Always write the raw token JSON to --out (consumed by other commands).
      _write_json(token, args.out)
      if getattr(args, "json", False):
        _emit_ok_json(
          "approved",
          {
            "code": "OK",
            "tokenId": token.get("id"),
            "expiresAt": (token.get("scope") or {}).get("expiresAt"),
            "scope": token.get("scope") or {},
          },
          None,
        )
      return

    if args.cmd == "verify-token":
      secret = os.environ.get("APPROVAL_HMAC_SECRET", "")
      if not secret:
        _fail("APPROVAL_HMAC_SECRET_REQUIRED", "APPROVAL_HMAC_SECRET is required")
      tok = _read_json(args.token)
      ok, code = verify_token(tok, secret)
      if getattr(args, "json", False):
        if ok:
          _emit_ok_json(
            "verified",
            {
              "code": code,
              "tokenId": tok.get("id"),
              "scope": tok.get("scope", {}),
            },
            getattr(args, "out", None),
          )
        else:
          _emit_error_json(
            code,
            "approval token invalid",
            {
              "tokenId": tok.get("id"),
              "scope": tok.get("scope", {}),
            },
            getattr(args, "out", None),
          )
        return
      _write_json({"ok": ok, "reason": code, "tokenId": tok.get("id"), "scope": tok.get("scope", {})}, getattr(args, "out", None))
      return

    if args.cmd == "open-pr":
      # v1.2: open PR if possible; otherwise return fallback URL on PAT-limited 403
      secret = os.environ.get("APPROVAL_HMAC_SECRET", "")
      if not secret:
        _fail("APPROVAL_HMAC_SECRET_REQUIRED", "APPROVAL_HMAC_SECRET is required")

      gh_token = os.environ.get("GITHUB_TOKEN", "")
      if not gh_token:
        _fail("GITHUB_TOKEN_REQUIRED", "GITHUB_TOKEN is required")

      proposal = _read_json(args.proposal)
      approval = _read_json(args.approval_token)

      ok, code = verify_token(approval, secret)
      if not ok:
        _audit("APPROVAL_DENIED", {"code": code, "repo": proposal.get("metadata", {}).get("repo"), "base": proposal.get("metadata", {}).get("baseBranch"), "tokenId": approval.get("id")})
        if getattr(args, "json", False):
          _emit_error_json(code, "approval token invalid", {"repo": proposal.get("metadata", {}).get("repo"), "base": proposal.get("metadata", {}).get("baseBranch"), "tokenId": approval.get("id")}, args.out)
          return
        raise SystemExit(f"approval token invalid: {code}")
      _audit("APPROVAL_VERIFIED", {"repo": proposal.get("metadata", {}).get("repo"), "base": proposal.get("metadata", {}).get("baseBranch"), "tokenId": approval.get("id")})

      repo = proposal["metadata"]["repo"]
      base = proposal["metadata"]["baseBranch"]

      actor = (args.actor or os.environ.get("CG_ACTOR") or os.environ.get("GITHUB_ACTOR") or "").strip()
      if not actor:
        _fail("CG_ACTOR_REQUIRED", "--actor or CG_ACTOR/GITHUB_ACTOR env is required", envKeys=["CG_ACTOR","GITHUB_ACTOR"])

      _require_scope(approval, repo, base, "open_pr", actor=actor)

      head = proposal["metadata"].get("headBranch") or os.environ.get("HEAD_BRANCH")
      if not head:
        _fail("HEAD_BRANCH_REQUIRED", "proposal.metadata.headBranch or HEAD_BRANCH env is required", envKeys=["HEAD_BRANCH"])

      proposal_hash = canonical_proposal_hash(proposal)
      if (approval.get("scope") or {}).get("proposalHash") != proposal_hash:
        _fail("APPROVAL_SCOPE_MISMATCH", "token scope proposalHash mismatch", expected=proposal_hash, got=(approval.get("scope") or {}).get("proposalHash"))

      api, used_default_api = _get_github_api_base_url()
      pr_url = f"{api}/repos/{repo}/pulls"
      title = proposal["metadata"].get("title") or f"Proposal {proposal['metadata'].get('proposalId','') }"
      body = (proposal["metadata"].get("body") or "") + f"\n\nProposalHash: {proposal_hash}\nTokenId: {approval.get('id')}\n"

      _audit("PR_OPEN_ATTEMPTED", {"repo": repo, "base": base, "head": head, "githubApiBaseUrl": api, "usedDefaultApiBaseUrl": used_default_api, "tokenId": approval.get("id")})

      status, txt = _gh_request("POST", pr_url, gh_token, {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
      })

      if status in (200, 201):
        pr = json.loads(txt)
        _audit("PR_OPENED", {"repo": repo, "base": base, "head": head, "prUrl": pr.get("html_url"), "prNumber": pr.get("number")})
        if getattr(args, "json", False):
          _emit_ok_json(
            "opened",
            {
              "prUrl": pr.get("html_url"),
              "prNumber": pr.get("number"),
              "githubApiBaseUrl": api,
              "usedDefaultApiBaseUrl": used_default_api,
            },
            args.out,
          )
        else:
          _write_json({"status": "opened", "prUrl": pr.get("html_url"), "prNumber": pr.get("number")}, args.out)
        return

      # v1.2 fail-safe fallback:
      # - 401/403 should never strand the user; return a browser PR-create URL.
      # - 403 reason classification is best-effort (recommendation), not a hard dependency.
      if status in (401, 403):
        pr_create_url = f"https://github.com/{repo}/pull/new/{head}?expand=1"
        reason_obj = {"code": "GITHUB_401", "detail": "unauthorized"} if status == 401 else _classify_403(txt)
        _audit(
          "PR_OPEN_FALLBACK",
          {
            "repo": repo,
            "base": base,
            "head": head,
            "prCreateUrl": pr_create_url,
            "status": status,
            "reason": reason_obj,
            "message": (txt or "")[:300],
          },
        )
        out_obj = {
          "status": "fallback",
          "prCreateUrl": pr_create_url,
          "reason": reason_obj,
          "githubApiBaseUrl": api,
          "usedDefaultApiBaseUrl": used_default_api,
        }
        if getattr(args, "json", False):
          _emit_ok_json("fallback", out_obj, args.out)
        else:
          _write_json(out_obj, args.out)
        return

      _audit("PR_OPEN_FAILED", {"repo": repo, "base": base, "head": head, "status": status, "message": (txt or "")[:300]})
      if getattr(args, "json", False):
        _emit_error_json("GITHUB_REQUEST_FAILED", "open-pr failed", {"repo": repo, "base": base, "head": head, "status": status, "message": (txt or "")[:300]}, args.out)
        return
      raise SystemExit(f"open-pr failed: status={status} body={(txt or '')[:300]}")

  except CGError as e:
    if getattr(args, "json", False):
      _emit(e.to_json(), getattr(args, "out", None))
      return
    raise
  except SystemExit as e:
    if getattr(args, "json", False):
      msg = str(e)
      _emit_error_json("CG_SYSTEM_EXIT", msg or "system exit", {"cmd": getattr(args, "cmd", "")}, getattr(args, "out", None))
      return
    raise

if __name__ == "__main__":
  main()
