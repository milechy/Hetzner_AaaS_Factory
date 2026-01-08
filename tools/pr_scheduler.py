"""
PR Scheduler - Ensures only one factory PR is open at a time on a given base branch.
"""
from __future__ import annotations
import requests


class PRScheduleBlocked(Exception):
    """Raised when a factory PR is already open on the target base branch."""
    pass


def assert_no_open_factory_pr(
    repo: str,
    base_branch: str,
    api_base: str,
    gh_token: str
) -> None:
    """
    Verify that no factory PR (proposal/*) is currently open on the base branch.
    
    Fail-Safe: On API errors, logs warning and returns (does not block).
    
    Args:
        repo: GitHub repository in format "owner/repo"
        base_branch: Target base branch (e.g., "main")
        api_base: GitHub API base URL (e.g., "https://api.github.com")
        gh_token: GitHub personal access token
        
    Raises:
        PRScheduleBlocked: If one or more factory PRs are already open
    """
    url = f"{api_base}/repos/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "state": "open",
        "per_page": 100
    }
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Fail-Safe: if API returns non-200, log warning and return
        if r.status_code != 200:
            print(f"[PRSchedule] warning: skip check status={r.status_code}")
            return
        
        prs = r.json()
    except Exception as e:
        # Fail-Safe: on any exception, log warning and return
        print(f"[PRSchedule] warning: skip check exception={type(e).__name__}")
        return
    
    # Filter for factory PRs: head ref starts with "proposal/" and base matches
    factory_prs = [
        pr for pr in prs
        if pr["head"]["ref"].startswith("proposal/") and pr["base"]["ref"] == base_branch
    ]
    
    if factory_prs:
        count = len(factory_prs)
        first_pr = factory_prs[0]
        first_url = first_pr.get("html_url") or first_pr.get("url", "unknown")
        msg = f"PR_ALREADY_OPEN count={count} base={base_branch} first={first_url}"
        print(f"[PRSchedule] blocked reason=existing_open_factory_pr count={count} base={base_branch} first={first_url}")
        raise PRScheduleBlocked(msg)
