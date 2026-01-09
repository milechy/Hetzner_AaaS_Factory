from __future__ import annotations
import os, json, base64, uuid
import requests
import hmac, hashlib
from datetime import datetime, timezone
from tools.pr_scheduler import assert_no_open_factory_pr, PRScheduleBlocked

def stable_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def sign(payload: dict, secret: str) -> str:
    msg = stable_json(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return "hmac-sha256:" + sig

def verify_approval(token: dict, secret: str, repo: str, base: str, proposal_hash: str) -> None:
    if "signature" not in token:
        raise SystemExit("APPROVAL_INVALID: missing signature")
    payload = {k: token[k] for k in token.keys() if k != "signature"}
    expected = sign(payload, secret)
    if token["signature"] != expected:
        raise SystemExit("APPROVAL_INVALID: signature mismatch")
    scope = token.get("scope", {})
    if scope.get("repo") != repo or scope.get("baseBranch") != base or scope.get("proposalHash") != proposal_hash:
        raise SystemExit("APPROVAL_INVALID: scope mismatch")
    exp = scope.get("expiresAt")
    if not exp:
        raise SystemExit("APPROVAL_INVALID: expiresAt missing")
    exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
    if datetime.now(timezone.utc) >= exp_dt:
        raise SystemExit("APPROVAL_EXPIRED")

def gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

def b64_decode(s: str) -> bytes:
    return base64.b64decode(s.encode("utf-8"))

def b64_encode(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")

def main():
    # Inputs
    proposal = json.load(open("proposal.json", "r", encoding="utf-8"))
    approval_req = json.load(open("approval_request.json", "r", encoding="utf-8"))
    approval = json.load(open("approval_token.json", "r", encoding="utf-8"))

    repo = proposal["metadata"]["repo"]
    base = proposal["metadata"]["baseBranch"]
    proposal_hash = approval_req["normalizedProposalHash"]

    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        raise SystemExit("Missing env: GITHUB_TOKEN")
    secret = os.environ.get("APPROVAL_HMAC_SECRET")
    if not secret:
        raise SystemExit("Missing env: APPROVAL_HMAC_SECRET")

    # Verify approval token binding
    verify_approval(approval, secret, repo, base, proposal_hash)

    # Create branch
    branch_name = f"proposal/{proposal['metadata']['proposalId']}"
    api = "https://api.github.com"

    # get base sha
    ref_url = f"{api}/repos/{repo}/git/ref/heads/{base}"
    r = requests.get(ref_url, headers=gh_headers(gh_token), timeout=30)
    r.raise_for_status()
    base_sha = r.json()["object"]["sha"]

    # Check for open factory PRs BEFORE any write operations
    try:
        assert_no_open_factory_pr(repo=repo, base_branch=base, api_base=api, gh_token=gh_token)
    except PRScheduleBlocked as e:
        print(f"[PRSchedule] blocked {e}")
        raise SystemExit(2)

    # create new ref
    create_ref_url = f"{api}/repos/{repo}/git/refs"
    payload = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
    r = requests.post(create_ref_url, json=payload, headers=gh_headers(gh_token), timeout=30)
    if r.status_code == 422:
        # branch may already exist; continue
        pass
    else:
        r.raise_for_status()

    # Update docs/README.md by appending a line
    target_path = "docs/README.md"
    content_url = f"{api}/repos/{repo}/contents/{target_path}"

    r = requests.get(content_url, headers=gh_headers(gh_token), params={"ref": branch_name}, timeout=30)
    if r.status_code == 404:
        raise SystemExit("docs/README.md not found in repo (expected for this demo). Adjust target_path.")
    r.raise_for_status()
    data = r.json()
    old_b = b64_decode(data["content"].replace("\n", ""))
    old_text = old_b.decode("utf-8", errors="replace")

    append_line = f"\n\n- ControlledGitTools v1.2 wiring check ({datetime.now(timezone.utc).date().isoformat()})\n"
    new_text = old_text.rstrip("\n") + append_line
    new_b64 = b64_encode(new_text.encode("utf-8"))

    put_payload = {
        "message": f"Docs: wiring check via controlled git ({proposal['metadata']['proposalId']})",
        "content": new_b64,
        "sha": data["sha"],
        "branch": branch_name,
    }
    r = requests.put(content_url, json=put_payload, headers=gh_headers(gh_token), timeout=30)
    r.raise_for_status()

    # Open PR
    pr_url = f"{api}/repos/{repo}/pulls"
    pr_payload = {
        "title": proposal["metadata"].get("title") or f"Proposal {proposal['metadata']['proposalId']}",
        "body": (proposal["metadata"].get("body") or "") + f"\n\nProposalHash: {proposal_hash}\nTokenId: {approval.get('id')}\n",
        "head": branch_name,
        "base": base,
    }
    r = requests.post(pr_url, json=pr_payload, headers=gh_headers(gh_token), timeout=30)
    r.raise_for_status()
    pr = r.json()

    # Add labels (best-effort)
    labels_url = f"{api}/repos/{repo}/issues/{pr['number']}/labels"
    requests.post(labels_url, json={"labels": ["proposal-only", "needs-review"]}, headers=gh_headers(gh_token), timeout=30)

    print("PR created:", pr["html_url"])

if __name__ == "__main__":
    main()
