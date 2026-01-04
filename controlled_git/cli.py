from __future__ import annotations
import argparse, json, os, uuid
from datetime import datetime, timedelta, timezone
import hmac, hashlib

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
  approve.add_argument("--minutes", type=int, default=60)
  approve.add_argument("--out")

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

if __name__ == "__main__":
  main()
