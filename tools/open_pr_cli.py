from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone

# requests is preferred, but this repo must remain runnable in minimal envs.
# If `requests` is unavailable, fall back to a tiny stdlib-based shim that supports
# the subset we use (get/post/put/delete + json() + raise_for_status()).
try:
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import json as _json
    import urllib.error as _urlerr
    import urllib.parse as _urlparse
    import urllib.request as _urlreq

    class _Resp:
        def __init__(self, status_code: int, body: bytes):
            self.status_code = status_code
            self._body = body

        def json(self):
            if not self._body:
                return None
            return _json.loads(self._body.decode("utf-8"))

        @property
        def text(self) -> str:
            return self._body.decode("utf-8", errors="replace")

        def raise_for_status(self) -> None:
            if 400 <= self.status_code:
                raise RuntimeError(f"HTTP {self.status_code}: {self.text}")

    def _request(method: str, url: str, *, headers=None, params=None, json=None, timeout=30):
        hdrs = dict(headers or {})
        if params:
            q = _urlparse.urlencode(params)
            url = url + ("&" if "?" in url else "?") + q
        data = None
        if json is not None:
            data = _json.dumps(json).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        req = _urlreq.Request(url, data=data, headers=hdrs, method=method)
        try:
            with _urlreq.urlopen(req, timeout=timeout) as resp:
                return _Resp(int(resp.getcode()), resp.read())
        except _urlerr.HTTPError as e:
            return _Resp(int(e.code), e.read())

    class requests:  # noqa: N801
        @staticmethod
        def get(url, headers=None, params=None, timeout=30):
            return _request("GET", url, headers=headers, params=params, timeout=timeout)

        @staticmethod
        def post(url, headers=None, params=None, json=None, timeout=30):
            return _request("POST", url, headers=headers, params=params, json=json, timeout=timeout)

        @staticmethod
        def put(url, headers=None, params=None, json=None, timeout=30):
            return _request("PUT", url, headers=headers, params=params, json=json, timeout=timeout)

        @staticmethod
        def delete(url, headers=None, params=None, json=None, timeout=30):
            return _request("DELETE", url, headers=headers, params=params, json=json, timeout=timeout)


from tools.pr_scheduler import PRScheduleBlocked, assert_no_open_factory_pr
from tools.repo_lock import RepoLock, RepoLockError

# Import canonical hash from controlled_git if available
try:
    from controlled_git.cli import canonical_proposal_hash
except ImportError:
    def canonical_proposal_hash(proposal: dict) -> str:
        """Fallback implementation if controlled_git is not available."""
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
        raw = stable_json(minimal).encode("utf-8")
        return "sha256:" + hashlib.sha256(raw).hexdigest()


def stable_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sign(payload: dict, secret: str) -> str:
    msg = stable_json(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return "hmac-sha256:" + sig


def verify_approval(token: dict, secret: str, repo: str, base: str, proposal_hash: str, actor: str) -> None:
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

    # Verify actor matches
    token_actor = scope.get("actorId")
    if not token_actor:
        raise SystemExit("APPROVAL_INVALID: actorId missing in token scope")
    if token_actor != actor:
        raise SystemExit("APPROVAL_ACTOR_MISMATCH: token actorId does not match")


def gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def b64_decode(s: str) -> bytes:
    return base64.b64decode(s.encode("utf-8"))


def b64_encode(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def apply_file_changes(proposal: dict, repo: str, branch_name: str, api: str, gh_token: str, dry_run: bool) -> None:
    """Apply file changes from proposal to the branch."""
    files = proposal.get("changes", {}).get("files", [])

    # Check for patch-only files
    patch_only_paths = []
    for file_entry in files:
        if not file_entry.get("path"):
            raise SystemExit("ERROR: file entry missing 'path' field")

        has_content_b64 = "content_b64" in file_entry
        has_delete = file_entry.get("delete", False)
        has_patch = "patch" in file_entry

        # If only patch is provided (no content_b64 or delete), it's patch-only
        if has_patch and not has_content_b64 and not has_delete:
            patch_only_paths.append(file_entry["path"])

    if patch_only_paths:
        print(f"[OpenPR] ERROR: PATCH_NOT_SUPPORTED")
        print(f"[OpenPR] patch-only files detected (not supported): {', '.join(patch_only_paths)}")
        raise SystemExit(10)  # Exit code 10 for PATCH_NOT_SUPPORTED

    # Apply changes
    for file_entry in files:
        path = file_entry["path"]
        content_url = f"{api}/repos/{repo}/contents/{path}"

        if file_entry.get("delete", False):
            # DELETE operation
            if dry_run:
                print(f"[OpenPR] dry-run: would DELETE {path}")
                continue

            # Get current file SHA
            r = requests.get(content_url, headers=gh_headers(gh_token), params={"ref": branch_name}, timeout=30)
            if r.status_code == 404:
                print(f"[OpenPR] warn: file not found for deletion: {path}")
                continue
            r.raise_for_status()
            file_sha = r.json()["sha"]

            # Delete the file
            delete_payload = {
                "message": f"Delete {path}",
                "sha": file_sha,
                "branch": branch_name,
            }
            r = requests.delete(content_url, json=delete_payload, headers=gh_headers(gh_token), timeout=30)
            r.raise_for_status()
            print(f"[OpenPR] deleted {path}")

        elif "content_b64" in file_entry:
            # PUT operation (create or update)
            if dry_run:
                print(f"[OpenPR] dry-run: would PUT {path}")
                continue

            # Get current file SHA if it exists
            r = requests.get(content_url, headers=gh_headers(gh_token), params={"ref": branch_name}, timeout=30)
            file_sha = None
            if r.status_code == 200:
                file_sha = r.json()["sha"]
            elif r.status_code != 404:
                r.raise_for_status()

            # Create or update the file
            put_payload = {
                "message": f"Update {path}",
                "content": file_entry["content_b64"],
                "branch": branch_name,
            }
            if file_sha:
                put_payload["sha"] = file_sha

            r = requests.put(content_url, json=put_payload, headers=gh_headers(gh_token), timeout=30)
            r.raise_for_status()
            print(f"[OpenPR] updated {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Open PR from proposal")
    parser.add_argument("--proposal", required=True, help="Path to proposal JSON file")
    parser.add_argument("--approval-token", required=True, help="Path to approval token JSON file")
    parser.add_argument("--approval-request", help="Path to approval request JSON file (optional)")
    parser.add_argument("--api-base", help="GitHub API base URL (default: env GITHUB_API_BASE_URL or https://api.github.com)")
    parser.add_argument("--actor", help="Actor ID (default: env CG_ACTOR or GITHUB_ACTOR)")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no writes")

    args = parser.parse_args()

    # Load proposal
    with open(args.proposal, "r", encoding="utf-8") as f:
        proposal = json.load(f)

    # Load approval token
    with open(args.approval_token, "r", encoding="utf-8") as f:
        approval = json.load(f)

    # Compute proposal hash
    if args.approval_request:
        with open(args.approval_request, "r", encoding="utf-8") as f:
            approval_req = json.load(f)
        proposal_hash = approval_req["normalizedProposalHash"]
    else:
        proposal_hash = canonical_proposal_hash(proposal)

    repo = proposal["metadata"]["repo"]
    base = proposal["metadata"]["baseBranch"]
    head_branch = proposal["metadata"].get("headBranch")
    if not head_branch:
        head_branch = f"proposal/{proposal['metadata']['proposalId']}"

    # Get API base
    api = args.api_base or os.environ.get("GITHUB_API_BASE_URL") or "https://api.github.com"
    api = api.rstrip("/")

    # Get actor
    actor = args.actor or os.environ.get("CG_ACTOR") or os.environ.get("GITHUB_ACTOR")
    if not actor:
        raise SystemExit("ERROR: --actor or env CG_ACTOR/GITHUB_ACTOR is required")

    # Get tokens
    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        raise SystemExit("ERROR: Missing env: GITHUB_TOKEN")

    secret = os.environ.get("APPROVAL_HMAC_SECRET")
    if not secret:
        raise SystemExit("ERROR: Missing env: APPROVAL_HMAC_SECRET")

    # Verify approval token binding
    verify_approval(approval, secret, repo, base, proposal_hash, actor)

    if args.dry_run:
        print(f"[OpenPR] dry-run: validation passed for repo={repo} base={base} head={head_branch}")
        print(f"[OpenPR] dry-run: would apply {len(proposal.get('changes', {}).get('files', []))} file changes")
        apply_file_changes(proposal, repo, head_branch, api, gh_token, dry_run=True)
        return

    # Get base sha
    ref_url = f"{api}/repos/{repo}/git/ref/heads/{base}"
    r = requests.get(ref_url, headers=gh_headers(gh_token), timeout=30)
    r.raise_for_status()
    base_sha = r.json()["object"]["sha"]

    # PRSchedule gate: must run BEFORE any write operations
    try:
        assert_no_open_factory_pr(repo=repo, base_branch=base, api_base=api, gh_token=gh_token)
    except PRScheduleBlocked:
        print(f"[PRSchedule] exit=2 blocked repo={repo} base={base}")
        raise SystemExit(2)

    # RepoLock gate: any write operations must be executed under lock
    lock = RepoLock(repo=repo, api_base=api, gh_token=gh_token, ttl_seconds=3600)
    try:
        lock.acquire(sha=base_sha)
    except RepoLockError:
        print(f"[RepoLock] exit=3 locked repo={repo} ref={lock.lock_ref}")
        raise SystemExit(3)

    try:
        # Create new ref
        create_ref_url = f"{api}/repos/{repo}/git/refs"
        payload = {"ref": f"refs/heads/{head_branch}", "sha": base_sha}
        r = requests.post(create_ref_url, json=payload, headers=gh_headers(gh_token), timeout=30)
        if r.status_code != 422:
            r.raise_for_status()

        # Apply file changes from proposal
        apply_file_changes(proposal, repo, head_branch, api, gh_token, dry_run=False)

        # Open PR
        pr_url = f"{api}/repos/{repo}/pulls"
        pr_payload = {
            "title": proposal["metadata"].get("title") or f"Proposal {proposal['metadata']['proposalId']}",
            "body": (proposal["metadata"].get("body") or "")
            + f"\n\nProposalHash: {proposal_hash}\nTokenId: {approval.get('id')}\n",
            "head": head_branch,
            "base": base,
        }
        r = requests.post(pr_url, json=pr_payload, headers=gh_headers(gh_token), timeout=30)
        r.raise_for_status()
        pr = r.json()

        # Add labels (best-effort)
        labels_url = f"{api}/repos/{repo}/issues/{pr['number']}/labels"
        requests.post(
            labels_url,
            json={"labels": ["proposal-only", "needs-review"]},
            headers=gh_headers(gh_token),
            timeout=30,
        )

        print(f"[OpenPR] created repo={repo} base={base} head={head_branch} url={pr['html_url']}")

    finally:
        try:
            lock.release()
        except RepoLockError:
            print(f"[RepoLock] release warn reason=release_failed repo={repo} ref={lock.lock_ref}")


if __name__ == "__main__":
    main()
