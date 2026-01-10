"""tools.pr_scheduler

PR Scheduler - Ensures only one factory PR is open at a time on a given base branch.

Fail-safe behavior:
- On GitHub API errors (non-200) or exceptions, the check is skipped (warn-only).
- Only blocks when it can positively confirm an existing open factory PR.
"""

from __future__ import annotations

# requests is preferred, but tests and minimal runtimes must work without it.
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

    def _request(method: str, url: str, *, headers=None, params=None, timeout=30):
        hdrs = dict(headers or {})
        if params:
            q = _urlparse.urlencode(params)
            url = url + ("&" if "?" in url else "?") + q
        req = _urlreq.Request(url, headers=hdrs, method=method)
        try:
            with _urlreq.urlopen(req, timeout=timeout) as resp:
                return _Resp(int(resp.getcode()), resp.read())
        except _urlerr.HTTPError as e:
            return _Resp(int(e.code), e.read())

    class requests:  # noqa: N801
        @staticmethod
        def get(url, headers=None, params=None, timeout=30):
            return _request("GET", url, headers=headers, params=params, timeout=timeout)


class PRScheduleBlocked(Exception):
    """Raised when a factory PR is already open on the target base branch."""


def assert_no_open_factory_pr(
    repo: str,
    base_branch: str,
    api_base: str,
    gh_token: str,
) -> None:
    """Verify that no factory PR (proposal/*) is currently open on the base branch.

    Fail-Safe: On API errors, logs warning and returns (does not block).

    Args:
        repo: GitHub repository in format "owner/repo"
        base_branch: Target base branch (e.g., "main")
        api_base: GitHub API base URL (e.g., "https://api.github.com")
        gh_token: GitHub personal access token

    Raises:
        PRScheduleBlocked: If one or more factory PRs are already open
    """

    api_base = api_base.rstrip("/")
    url = f"{api_base}/repos/{repo}/pulls"

    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "state": "open",
        "per_page": 100,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)

        # Fail-Safe: if API returns non-200, log warning and return
        if r.status_code != 200:
            print(f"[PRSchedule] warn reason=github_api_non_200 repo={repo} base={base_branch} status={r.status_code}")
            return

        prs = r.json()

    except Exception as e:
        # Fail-Safe: on any exception, log warning and return
        print(f"[PRSchedule] warn reason=github_api_exception repo={repo} base={base_branch} exc={type(e).__name__}")
        return

    # Filter for factory PRs: head ref starts with "proposal/" and base matches
    factory_prs = [
        pr
        for pr in prs
        if pr["head"]["ref"].startswith("proposal/") and pr["base"]["ref"] == base_branch
    ]

    if factory_prs:
        count = len(factory_prs)
        first_pr = factory_prs[0]
        first_url = first_pr.get("html_url") or first_pr.get("url", "unknown")

        msg = f"PR_ALREADY_OPEN count={count} base={base_branch} first={first_url}"
        print(
            f"[PRSchedule] blocked reason=existing_open_factory_pr repo={repo} base={base_branch} count={count} first={first_url}"
        )
        raise PRScheduleBlocked(msg)
