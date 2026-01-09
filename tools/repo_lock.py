"""tools.repo_lock

RepoLock - Fail-fast distributed lock for OpenPR execution on the same repo.

Lock strategy:
- Acquire: create a Git ref (lock branch) in the target repo
- Release: delete the lock ref

Fail-fast:
- If lock exists (422), raise RepoLockError (caller should exit immediately)
"""

from __future__ import annotations

import requests


class RepoLockError(Exception):
    pass


class RepoLock:
    def __init__(
        self,
        repo: str,
        api_base: str,
        gh_token: str,
        lock_ref: str = "refs/heads/__factory_lock__/open_pr",
        timeout: int = 30,
    ) -> None:
        self.repo = repo
        self.api_base = api_base.rstrip("/")
        self.gh_token = gh_token
        self.lock_ref = lock_ref
        self.timeout = timeout

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github+json",
        }

    def acquire(self, sha: str) -> None:
        """Acquire lock by creating lock ref pointing to sha.

        Success: 201/200
        Already exists: 422 -> RepoLockError (fail-fast)
        Other errors: RepoLockError
        """
        url = f"{self.api_base}/repos/{self.repo}/git/refs"
        payload = {"ref": self.lock_ref, "sha": sha}

        r = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)

        if r.status_code in (200, 201):
            print(f"[RepoLock] acquire ok repo={self.repo} ref={self.lock_ref}")
            return

        if r.status_code == 422:
            print(
                f"[RepoLock] acquire fail reason=already_locked repo={self.repo} ref={self.lock_ref} status=422"
            )
            raise RepoLockError("REPO_LOCKED")

        print(
            f"[RepoLock] acquire fail reason=github_api_error repo={self.repo} ref={self.lock_ref} status={r.status_code}"
        )
        raise RepoLockError(f"REPO_LOCK_ACQUIRE_FAILED status={r.status_code}")

    def release(self) -> None:
        """Release lock by deleting lock ref.

        Success: 204
        Not found: 404 -> warn only (do not fail)
        Other errors: RepoLockError
        """
        ref_path = self.lock_ref
        if ref_path.startswith("refs/"):
            ref_path = ref_path[len("refs/") :]

        url = f"{self.api_base}/repos/{self.repo}/git/refs/{ref_path}"
        r = requests.delete(url, headers=self._headers(), timeout=self.timeout)

        if r.status_code == 204:
            print(f"[RepoLock] release ok repo={self.repo} ref={self.lock_ref}")
            return

        if r.status_code == 404:
            print("[RepoLock] release warn reason=not_found (may have been manually deleted)")
            return

        print(
            f"[RepoLock] release fail reason=github_api_error repo={self.repo} ref={self.lock_ref} status={r.status_code}"
        )
        raise RepoLockError(f"REPO_LOCK_RELEASE_FAILED status={r.status_code}")