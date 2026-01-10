"""RepoLock

Fail-fast distributed lock for OpenPR execution on the same repo.

Implementation:
- Lock is represented as a Git ref under:
    refs/heads/__factory_lock__/open_pr/<epoch_seconds>
- Acquire is fail-fast when an active lock exists.
- Optional TTL: expired locks are reaped (deleted) before acquiring.

This module is intentionally dependency-light. If `requests` is not installed,
we still expose a `requests` symbol so unit tests can patch it; runtime calls
will raise a clear error.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class _RequestsShim:
    """Fallback shim when `requests` is not installed.

    Unit tests patch `tools.repo_lock.requests.<method>`; this shim preserves the
    attribute surface so patching works.
    """

    def _missing(self) -> None:
        raise ModuleNotFoundError("requests is required to use RepoLock at runtime")

    def get(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        self._missing()

    def post(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        self._missing()

    def delete(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        self._missing()


try:
    import requests as _requests  # type: ignore

    requests = _requests
except ModuleNotFoundError:  # pragma: no cover
    requests = _RequestsShim()  # type: ignore


class RepoLockError(Exception):
    """Raised when RepoLock cannot be acquired or released safely."""


@dataclass
class RepoLock:
    repo: str
    api_base: str
    gh_token: str
    ttl_seconds: int = 0

    # Set after acquire
    lock_ref: Optional[str] = None

    @property
    def lock_prefix(self) -> str:
        # Logical namespace; stored as refs/heads/... in GitHub.
        return "refs/heads/__factory_lock__/open_pr"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github+json",
        }

    def _matching_refs_url(self) -> str:
        # GitHub API expects the path without the leading "refs/".
        # matching-refs supports prefixes such as "heads/<prefix>".
        return f"{self.api_base}/repos/{self.repo}/git/matching-refs/heads/__factory_lock__/open_pr"

    def _delete_ref_url(self, full_ref: str) -> str:
        # DELETE expects e.g. heads/__factory_lock__/open_pr/1234
        ref_path = full_ref
        if ref_path.startswith("refs/"):
            ref_path = ref_path[len("refs/") :]
        return f"{self.api_base}/repos/{self.repo}/git/refs/{ref_path}"

    def _create_ref_url(self) -> str:
        return f"{self.api_base}/repos/{self.repo}/git/refs"

    def _parse_epoch_from_ref(self, ref: str) -> Optional[int]:
        # Expect refs/heads/__factory_lock__/open_pr/<epoch>
        parts = ref.split("/")
        if not parts:
            return None
        try:
            return int(parts[-1])
        except Exception:
            return None

    def _list_existing_locks(self) -> List[str]:
        r = requests.get(self._matching_refs_url(), headers=self._headers(), timeout=30)
        if r.status_code != 200:
            raise RepoLockError(f"REPO_LOCK_LIST_FAILED status={r.status_code}")

        data = r.json()
        if not isinstance(data, list):
            return []
        refs: List[str] = []
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("ref"), str):
                refs.append(item["ref"])
        return refs

    def _reap_expired_locks(self, now: int, refs: List[str]) -> None:
        # TTL disabled => do not reap.
        if self.ttl_seconds <= 0:
            return

        for ref in refs:
            epoch = self._parse_epoch_from_ref(ref)
            if epoch is None:
                # Unknown format: treat as active (do not delete).
                continue
            age = now - epoch
            if age <= self.ttl_seconds:
                continue

            # Expired: attempt delete. Any non-204/404 is a hard failure.
            dr = requests.delete(self._delete_ref_url(ref), headers=self._headers(), timeout=30)
            if dr.status_code in (204, 404):
                continue

            print(
                f"[RepoLock] reap fail reason=github_api_error repo={self.repo} ref={ref} status={dr.status_code}"
            )
            raise RepoLockError(f"REPO_LOCK_REAP_FAILED status={dr.status_code}")

    def _has_active_lock(self, now: int, refs: List[str]) -> bool:
        # TTL disabled => any lock blocks.
        if self.ttl_seconds <= 0:
            return len(refs) > 0

        for ref in refs:
            epoch = self._parse_epoch_from_ref(ref)
            if epoch is None:
                # Unknown format: consider active.
                return True
            if (now - epoch) <= self.ttl_seconds:
                return True
        return False

    def acquire(self, sha: str, *, max_retries: int = 2) -> None:
        """Acquire the repo lock.

        Behavior:
        - List existing locks
        - Reap expired locks (if TTL enabled)
        - If any active lock exists, raise RepoLockError (fail-fast)
        - Create a new lock ref. If 422 collision, retry up to max_retries.
        """

        now = int(time.time())

        refs = self._list_existing_locks()
        self._reap_expired_locks(now, refs)

        # Re-list after reaping to avoid race/stale view.
        refs = self._list_existing_locks()
        if self._has_active_lock(now, refs):
            # Prefer a stable ref for logging (first found).
            first = refs[0] if refs else self.lock_prefix
            print(
                f"[RepoLock] acquire fail reason=already_locked repo={self.repo} ref={first} status=422"
            )
            raise RepoLockError("REPO_LOCKED")

        last_exc: Optional[RepoLockError] = None
        for _ in range(max_retries):
            ref = f"{self.lock_prefix}/{int(time.time())}"
            payload = {"ref": ref, "sha": sha}
            r = requests.post(
                self._create_ref_url(), json=payload, headers=self._headers(), timeout=30
            )

            if r.status_code == 201:
                self.lock_ref = ref
                print(f"[RepoLock] acquire ok repo={self.repo} ref={self.lock_ref}")
                return

            if r.status_code == 422:
                # Collision (another actor created a lock ref). Re-check locks.
                last_exc = RepoLockError("REPO_LOCK_COLLISION")
                continue

            print(
                f"[RepoLock] acquire fail reason=github_api_error repo={self.repo} ref={ref} status={r.status_code}"
            )
            raise RepoLockError(f"REPO_LOCK_ACQUIRE_FAILED status={r.status_code}")

        # Retries exhausted
        raise last_exc or RepoLockError("REPO_LOCK_COLLISION")

    def release(self) -> None:
        """Release the repo lock (best-effort for missing lock)."""

        if not self.lock_ref:
            return

        r = requests.delete(self._delete_ref_url(self.lock_ref), headers=self._headers(), timeout=30)

        if r.status_code == 204:
            print(f"[RepoLock] release ok repo={self.repo} ref={self.lock_ref}")
            self.lock_ref = None
            return

        if r.status_code == 404:
            print(
                f"[RepoLock] release warn reason=not_found repo={self.repo} ref={self.lock_ref} (may have been manually deleted)"
            )
            self.lock_ref = None
            return

        print(
            f"[RepoLock] release fail reason=github_api_error repo={self.repo} ref={self.lock_ref} status={r.status_code}"
        )
        raise RepoLockError(f"REPO_LOCK_RELEASE_FAILED status={r.status_code}")