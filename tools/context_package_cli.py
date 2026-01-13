# tools/context_package_cli.py
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import tools.context_package as context_package
from tools.repo_lock import RepoLock, RepoLockError
from tools.work_queue import SchemaError, InvariantViolation, derive_queue_state


# ContextPackage Spec v1 §10A: SSOT branch for materialized ContextPackage documents
CONTEXTS_SSOT_BRANCH = "__factory_state__/contexts"

# ContextPackage Spec v1: Work Queue SSOT source branch and path
QUEUE_SSOT_BRANCH = "__factory_state__/queue"
QUEUE_SSOT_PATH = "factory/queue/events.jsonl"


# --- Compatibility layer ---
# `tools.context_package` is the SSOT implementation, but symbols may evolve.
# This CLI must remain runnable even if some names are not exported.


class _ContextSchemaError(Exception):
    pass


class _ContextInvariantViolation(Exception):
    pass


ContextSchemaError = getattr(context_package, "ContextSchemaError", _ContextSchemaError)
ContextInvariantViolation = getattr(
    context_package, "ContextInvariantViolation", _ContextInvariantViolation
)


def now_rfc3339_utc() -> str:
    fn = getattr(context_package, "now_rfc3339_utc", None)
    if callable(fn):
        return fn()
    import datetime

    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def validate_context_id(context_id: str) -> None:
    fn = getattr(context_package, "validate_context_id", None)
    if callable(fn):
        fn(context_id)
        return
    if not context_id.startswith("ctx_"):
        raise ContextSchemaError("context_id_must_start_with_ctx_")


def contexts_path_for(context_id: str) -> str:
    fn = getattr(context_package, "contexts_path_for", None)
    if callable(fn):
        return fn(context_id)
    return str(Path("factory") / "contexts" / f"{context_id}.json")


def build_context_package(*, context_id: str, created_at: str, inputs: Any) -> Dict[str, Any]:
    fn = getattr(context_package, "build_context_package", None)
    if not callable(fn):
        return {
            "contextId": context_id,
            "createdAt": created_at,
            "jobId": getattr(inputs, "job_id", ""),
        }

    try:
        return fn(context_id=context_id, created_at=created_at, inputs=inputs)
    except TypeError:
        pass

    try:
        return fn(
            context_id=context_id,
            created_at=created_at,
            queue_events=getattr(inputs, "queue_events", None),
            job_id=getattr(inputs, "job_id", None),
            derived_state=getattr(inputs, "derived_state", None),
        )
    except TypeError:
        pass

    return fn(context_id, created_at, inputs)


class _ContextBuildInputs:
    def __init__(
        self,
        *,
        queue_events: List[Dict[str, Any]],
        job_id: str,
        derived_state: Any,
        require_head_only: bool = True,
    ) -> None:
        self.queue_events = queue_events
        self.job_id = job_id
        self.derived_state = derived_state
        self.require_head_only = require_head_only


ContextBuildInputs = getattr(context_package, "ContextBuildInputs", _ContextBuildInputs)


EXIT_BLOCKED = 2
EXIT_LOCK_FAIL = 3
EXIT_INVARIANT = 4


def _run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def _run_check(cmd: List[str]) -> None:
    p = _run(cmd)
    if p.returncode != 0:
        raise RuntimeError(
            f"cmd_failed cmd={' '.join(cmd)} rc={p.returncode} stderr={p.stderr.strip()}"
        )


def _current_branch() -> str:
    p = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if p.returncode != 0:
        return ""
    return (p.stdout or "").strip()


def _switch_back(branch: str) -> None:
    if not branch:
        return
    _run_check(["git", "checkout", branch])


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

    _run_check(["git", "checkout", "-B", CONTEXTS_SSOT_BRANCH])


def _push_contexts_branch() -> None:
    _run_check(["git", "push", "-u", "origin", f"HEAD:{CONTEXTS_SSOT_BRANCH}"])


def _parse_queue_events_from_ssot() -> List[Dict[str, Any]]:
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
        events.append(obj)

    return events


def _make_default_context_id() -> str:
    import time

    unix = int(time.time())
    rand4 = os.urandom(2).hex()[:4]
    return f"ctx_{unix}_{rand4}"


def _queue_head_job_id(events: List[Dict[str, Any]]) -> str:
    for ev in events:
        if not isinstance(ev, dict):
            continue
        jid = (ev.get("jobId") or "").strip()
        if not jid:
            continue
        if (ev.get("type") or ev.get("eventType")) == "__init__":
            continue
        return jid
    return ""


def _job_is_blocked(events: List[Dict[str, Any]], job_id: str) -> bool:
    blocked = False
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if (ev.get("jobId") or "").strip() != job_id:
            continue
        t = ev.get("type") or ev.get("eventType")
        if t == "block":
            blocked = True
        elif t == "unblock":
            blocked = False
    return blocked


def _find_existing_context_by_job_id(job_id: str) -> str:
    base = Path("factory") / "contexts"
    if not base.exists():
        return ""
    for p in sorted(base.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(obj, dict) and (obj.get("jobId") or "").strip() == job_id:
            return (obj.get("contextId") or "").strip() or p.stem
    return ""


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    return (v or default).strip()


def _get_repo_config(args: Any) -> Dict[str, str]:
    repo = (getattr(args, "repo", "") or "").strip() or _env("GITHUB_REPOSITORY")
    token = (getattr(args, "gh_token", "") or "").strip() or _env("GITHUB_TOKEN")
    api_base = (getattr(args, "api_base", "") or "").strip() or _env(
        "GITHUB_API_BASE", "https://api.github.com"
    )

    if not repo:
        return {"repo": "", "gh_token": "", "api_base": api_base}
    return {"repo": repo, "gh_token": token, "api_base": api_base}


def _git_rev_parse(ref: str) -> str:
    p = _run(["git", "rev-parse", ref])
    if p.returncode != 0:
        return ""
    return (p.stdout or "").strip()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="context_package_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser(
        "materialize-ssot",
        help="Create ContextPackage JSON on __factory_state__/contexts (v1.7.0).",
    )
    m.add_argument("--actor", default=os.getenv("GITHUB_ACTOR", ""), help="Human actor (required).")
    m.add_argument("--job-id", required=True, help="Work Queue jobId (must be head and started).")
    m.add_argument(
        "--context-id",
        default="",
        help="Optional contextId (ctx_<unix>_<rand4>). Default: auto-generate.",
    )
    m.add_argument("--created-at", default="", help="Optional RFC3339 UTC (..Z). Default: now()")
    m.add_argument("--repo", default="", help="GitHub repo in owner/name (defaults to $GITHUB_REPOSITORY)")
    m.add_argument("--gh-token", default="", help="GitHub token (defaults to $GITHUB_TOKEN)")
    m.add_argument(
        "--api-base",
        default="",
        help="GitHub API base URL (defaults to https://api.github.com)",
    )

    return p.parse_args()


def main() -> None:
    args = _parse_args()
    orig_branch = _current_branch()

    if args.cmd != "materialize-ssot":
        raise SystemExit(1)

    actor = (args.actor or "").strip()
    if not actor:
        print("[ContextPackage] exit=4 reason=missing_actor", file=sys.stderr)
        raise SystemExit(EXIT_INVARIANT)
    if actor == "github-actions[bot]":
        print(
            "[ContextPackage] exit=4 reason=human_only actor=github-actions[bot]",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_INVARIANT)

    job_id = (args.job_id or "").strip()
    if not job_id:
        print("[ContextPackage] exit=4 reason=missing_job_id", file=sys.stderr)
        raise SystemExit(EXIT_INVARIANT)

    context_id = (args.context_id or "").strip() or _make_default_context_id()
    created_at = (args.created_at or "").strip() or now_rfc3339_utc()

    try:
        validate_context_id(context_id)
    except ContextSchemaError as e:
        print(
            f"[ContextPackage] exit=4 reason=context_id_invalid detail={e}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_INVARIANT)

    try:
        queue_events = _parse_queue_events_from_ssot()
        state = derive_queue_state(queue_events)

        cfg = _get_repo_config(args)
        if not cfg.get("repo") or not cfg.get("gh_token"):
            print("[ContextPackage] exit=4 reason=missing_repo_lock_config", file=sys.stderr)
            raise SystemExit(EXIT_INVARIANT)

        sha = _git_rev_parse("HEAD")
        if not sha:
            print("[ContextPackage] exit=4 reason=git_rev_parse_failed", file=sys.stderr)
            raise SystemExit(EXIT_INVARIANT)

        lock = RepoLock(
            repo=cfg["repo"],
            api_base=cfg["api_base"],
            gh_token=cfg["gh_token"],
            namespace="contexts",
            ttl_seconds=3600,
        )
        try:
            lock.acquire(sha)
        except RepoLockError as e:
            print(f"[RepoLock] exit=3 reason=locked detail={e}", file=sys.stderr)
            raise SystemExit(EXIT_LOCK_FAIL)

        head_job = _queue_head_job_id(queue_events)
        if head_job and head_job == job_id and _job_is_blocked(queue_events, job_id):
            print(f"[ContextPackage] exit=2 reason=head_blocked jobId={job_id}", file=sys.stderr)
            raise SystemExit(EXIT_BLOCKED)

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

        _switch_to_contexts_branch()

        existing_ctx = _find_existing_context_by_job_id(job_id)
        if existing_ctx:
            print(
                f"[ContextPackage] exit=4 reason=duplicate_job_materialization jobId={job_id} existingContextId={existing_ctx}",
                file=sys.stderr,
            )
            raise SystemExit(EXIT_INVARIANT)

        rel_path = contexts_path_for(context_id)
        path = Path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            print(f"[ContextPackage] exit=4 reason=context_file_exists path={rel_path}", file=sys.stderr)
            raise SystemExit(EXIT_INVARIANT)

        with open(path, "x", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")

        _run_check(["git", "add", rel_path])
        _run_check(["git", "commit", "-m", f"chore(context): materialize {context_id} for job {job_id}"])
        _push_contexts_branch()

        print(
            f"[ContextPackage] materialize ok contextId={context_id} jobId={job_id} branch={CONTEXTS_SSOT_BRANCH} path={rel_path}"
        )
    except (SchemaError, InvariantViolation) as e:
        print(
            f"[ContextPackage] exit=4 reason=queue_schema_or_invariant detail={e}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_INVARIANT)
    except (ContextSchemaError, ContextInvariantViolation) as e:
        print(
            f"[ContextPackage] exit=4 reason=invariant_or_schema detail={e}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_INVARIANT)
    except SystemExit:
        raise
    except Exception as e:
        print(f"[ContextPackage] exit=4 reason=unknown_error detail={e}", file=sys.stderr)
        raise SystemExit(EXIT_INVARIANT)
    finally:
        try:
            if "lock" in locals():
                lock.release()
        except Exception:
            pass
        try:
            _switch_back(orig_branch)
        except Exception:
            pass


if __name__ == "__main__":
    main()
