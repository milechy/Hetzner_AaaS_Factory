"""
RepoLock - Distributed lock using GitHub refs to prevent concurrent PR creation.
"""
from __future__ import annotations
import requests


class RepoLockError(Exception):
    """Raised when lock acquisition fails."""
    pass


class RepoLock:
    """
    Distributed lock that uses GitHub refs as a lock mechanism.
    
    The lock is held by creating a ref (branch) at a specific SHA.
    If the ref already exists, lock acquisition fails with RepoLockError.
    """
    
    def __init__(
        self,
        repo: str,
        api_base: str,
        gh_token: str,
        lock_ref: str = "refs/heads/__factory_lock__/open_pr"
    ):
        """
        Initialize RepoLock.
        
        Args:
            repo: GitHub repository in format "owner/repo"
            api_base: GitHub API base URL (e.g., "https://api.github.com")
            gh_token: GitHub personal access token
            lock_ref: Git ref to use as lock (default: refs/heads/__factory_lock__/open_pr)
        """
        self.repo = repo
        self.api_base = api_base
        self.gh_token = gh_token
        self.lock_ref = lock_ref
        
    def acquire(self, base_sha: str) -> None:
        """
        Acquire the lock by creating a ref at the given SHA.
        
        Args:
            base_sha: Git SHA to point the lock ref to
            
        Raises:
            RepoLockError: If lock is already held (ref already exists)
            requests.HTTPError: For other API errors
        """
        url = f"{self.api_base}/repos/{self.repo}/git/refs"
        headers = {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "ref": self.lock_ref,
            "sha": base_sha
        }
        
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if r.status_code == 422:
            raise RepoLockError("LOCK_ALREADY_HELD")
        
        r.raise_for_status()
        print(f"[RepoLock] acquire ok repo={self.repo} ref={self.lock_ref}")
        
    def release(self) -> None:
        """
        Release the lock by deleting the ref.
        
        If the ref doesn't exist (404), prints a warning and continues.
        
        Raises:
            requests.HTTPError: For API errors other than 404
        """
        # Extract the ref path without 'refs/heads/' prefix for DELETE endpoint
        ref_path = self.lock_ref.replace("refs/heads/", "")
        url = f"{self.api_base}/repos/{self.repo}/git/refs/heads/{ref_path}"
        headers = {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github+json",
        }
        
        r = requests.delete(url, headers=headers, timeout=30)
        
        if r.status_code == 404:
            print(f"[RepoLock] release warning: lock ref not found (may have been manually deleted)")
            return
        
        r.raise_for_status()
        print(f"[RepoLock] release ok repo={self.repo} ref={self.lock_ref}")
