# tools/context_package_cli.py
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from tools.context_package import (
    CONTEXTS_SSOT_BRANCH,
    QUEUE_SSOT_BRANCH,
    QUEUE_SSOT_PATH,
    ContextBuildInputs,
    ContextInvariantViolation,
    ContextSchemaError,
    build_context_package,
    contexts_path_for,
    now_rfc3339_utc,
    validate_context_id,
)
from tools.work_queue import SchemaError, InvariantViolation, derive_queue_state


def _run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def _run_check(cmd: List[str]) -> None:
    p = _run(cmd)
    if p.returncode != 0:
        raise RuntimeError(
            f"cmd_failed cmd={' '.join(cmd)} rc={p.returncode} stderr={p.stderr.strip()}"
        )


def _git_fetch(ref: str) -> None:
    _run_check(["git", "fetch", "origin", ref])


def _git_show(ref_path: str) -> str:
    p = _run(["git", "show", ref_path])
    if p.returncode != 0:
        raise RuntimeError(
            f"git_show_failed ref={ref_path} rc={p.returncode} stderr={p.stderr.strip()}"
        )
    return p.stdout


def _remote_branch_exists(branch: str) -> bool:
    p = _run(["git", "ls-remote", "--heads", "origin", branch])
    return p.returncode == 0 and bool(p.stdout.strip())


def _switch_to_contexts_branch() -> None:
    """Switch worktree to contexts SSOT branch.

    - If the remote branch exists: reset local branch to `origin/<branch>`.
    - If it does not exist: create a local branch from current HEAD.

    Important: do NOT `git fetch origin <branch>` when the branch does not exist.
    """

    if _remote_branch_exists(CONTEXTS_SSOT_BRANCH):
        _git_fetch(CONTEXTS_SSOT_BRANCH)
        _run_check(
            [
                "git",
                "checkout",
                "-B",
                CONTEXTS_SSOT_BRANCH,
                f"origin/{CONTEXTS_SSOT_BRANCH}",
            ]
        )
        return

    # Remote doesn't exist: create local branch from current HEAD
    _run_check(["git", "checkout", "-B", CONTEXTS_SSOT_BRANCH])


def _push_contexts_branch() -> None:
    _run_check(["git", "push", "-u", "origin", f"HEAD:{CONTEXTS_SSOT_BRANCH}"])


def _parse_queue_events_from_ssot() -> List[Dict[str, Any]]:
    # Read the queue SSOT file from origin branch without switching worktree
    _git_fetch(QUEUE_SSOT_BRANCH)
    raw = _git_show(f"origin/{QUEUE_SSOT_BRANCH}:{QUEUE_SSOT_PATH}")

    events: List[Dict[str, Any]] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        if not isinstance(obj, dict):
            raise SchemaError("jsonl_line_must_be_object")
        # allow __init__
        events.append(obj)

    return events


def _make_default_context_id() -> str:
    # ctx_<unix>_<rand4>
    import time

    unix = int(time.time())
    rand4 = os.urandom(2).hex()[:4]
    return f"ctx_{unix}_{rand4}"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="context_package_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser(
        "materialize-ssot",
        help="Create ContextPackage JSON on __factory_state__/contexts (v1.7.0).",
    )
    m.add_argument(
        "--actor",
        default=os.getenv("GITHUB_ACTOR", ""),
        help="Human actor (required).",
    )
    m.add_argument(
        "--job-id",
        required=True,
        help="Work Queue jobId (must be head and started).",
    )
    m.add_argument(
        "--context-id",
        default="",
        help="Optional contextId (ctx_<unix>_<rand4>). Default: auto-generate.",
    )
    m.add_argument(
        "--created-at",
        default="",
        help="Optional RFC3339 UTC (..Z). Default: now()",
    )

    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if args.cmd != "materialize-ssot":
        raise SystemExit(1)

    actor = (args.actor or "").strip()
    if not actor:
        print("[ContextPackage] exit=4 reason=missing_actor", file=sys.stderr)
        raise SystemExit(4)
    if actor == "github-actions[bot]":
        print(
            "[ContextPackage] exit=4 reason=human_only actor=github-actions[bot]",
            file=sys.stderr,
        )
        raise SystemExit(4)

    job_id = (args.job_id or "").strip()
    if not job_id:
        print("[ContextPackage] exit=4 reason=missing_job_id", file=sys.stderr)
        raise SystemExit(4)

    context_id = (args.context_id or "").strip() or _make_default_context_id()
    created_at = (args.created_at or "").strip() or now_rfc3339_utc()

    try:
        validate_context_id(context_id)
    except ContextSchemaError as e:
        print(f"[ContextPackage] exit=4 reason=context_id_invalid detail={e}", file=sys.stderr)
        raise SystemExit(4)

    # 1) Read queue SSOT
    try:
        queue_events = _parse_queue_events_from_ssot()
        state = derive_queue_state(queue_events)
    except (SchemaError, InvariantViolation) as e:
        print(f"[ContextPackage] exit=4 reason=queue_schema_or_invariant detail={e}", file=sys.stderr)
        raise SystemExit(4)

    # 2) Build doc (pure)
    try:
        doc = build_context_package(
            context_id=context_id,
            created_at=created_at,
            inputs=ContextBuildInputs(
                queue_events=queue_events,
                job_id=job_id,
                derived_state=state,
                require_head_only=True,
            ),
        )
    except (ContextSchemaError, ContextInvariantViolation) as e:
        print(f"[ContextPackage] exit=4 reason=invariant_or_schema detail={e}", file=sys.stderr)
        raise SystemExit(4)
    except Exception as e:
        print(f"[ContextPackage] exit=4 reason=unknown_error detail={e}", file=sys.stderr)
        raise SystemExit(4)

    # 3) Switch to contexts SSOT branch
    try:
        _switch_to_contexts_branch()
    except Exception as e:
        print(f"[ContextPackage] exit=4 reason=git_branch_switch_failed detail={e}", file=sys.stderr)
        raise SystemExit(4)

    # 4) Write file (create-only)
    rel_path = contexts_path_for(context_id)
    path = Path(rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        print(f"[ContextPackage] exit=4 reason=context_file_exists path={rel_path}", file=sys.stderr)
        raise SystemExit(4)

    with open(path, "x", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    # 5) Commit and push
    try:
        _run_check(["git", "add", rel_path])
        _run_check(["git", "commit", "-m", f"chore(context): materialize {context_id} for job {job_id}"])
        _push_contexts_branch()
    except Exception as e:
        print(f"[ContextPackage] exit=4 reason=git_commit_or_push_failed detail={e}", file=sys.stderr)
        raise SystemExit(4)

    print(
        f"[ContextPackage] materialize ok contextId={context_id} jobId={job_id} branch={CONTEXTS_SSOT_BRANCH} path={rel_path}"
    )


if __name__ == "__main__":
    main()