from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict

from tools.work_queue import (
    BOT_ACTOR,
    BlockedHead,
    HumanOnlyViolation,
    InvariantViolation,
    SchemaError,
    WorkQueueError,
    append_transition,
    enqueue,
)

DEFAULT_QUEUE_PATH = "factory/work_queue.jsonl"
DEFAULT_SSOT_BRANCH = "__factory_state__/work_queue"
DEFAULT_REMOTE = "origin"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="work_queue_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    enq = sub.add_parser("enqueue", help="Append an enqueue event (human only).")
    enq.add_argument("--queue-path", default=DEFAULT_QUEUE_PATH)
    enq.add_argument("--actor", default=os.getenv("GITHUB_ACTOR", ""), help="Human actor (required).")
    enq.add_argument("--kind", required=True, choices=["open_pr", "release", "changelog", "maintenance"])
    enq.add_argument("--repo", required=True, help="owner/name")
    enq.add_argument("--base", required=True, help="base branch, e.g. main")
    enq.add_argument(
        "--payload-json",
        help=(
            "JSON object string (must be a dict). "
            "Example: '{\"title\":\"...\"}'. "
            "NOTE: for --kind open_pr, payload.head is required (e.g. '{\"head\":\"feature/xxx\"}')."
        ),
        required=True,
    )

    tr = sub.add_parser("transition", help="Append a non-enqueue transition event (head-of-queue only).")
    tr.add_argument("--queue-path", default=DEFAULT_QUEUE_PATH)
    tr.add_argument("--actor", default=os.getenv("GITHUB_ACTOR", ""), help="Actor (required).")
    tr.add_argument("--type", required=True, choices=["start", "block", "unblock", "done", "fail", "cancel"])
    tr.add_argument("--job-id", required=True)
    tr.add_argument("--reason", default=None)
    tr.add_argument("--evidence", default=None)
    tr.add_argument("--meta-json", default=None, help="Optional JSON object string.")

    trssot = sub.add_parser(
        "transition-ssot",
        help="Append a non-enqueue transition event to the SSOT branch (head-of-queue only).",
    )
    trssot.add_argument("--ssot-branch", default=DEFAULT_SSOT_BRANCH)
    trssot.add_argument("--remote", default=DEFAULT_REMOTE)
    trssot.add_argument("--actor", default=os.getenv("GITHUB_ACTOR", ""), help="Actor (required).")
    trssot.add_argument("--type", required=True, choices=["start", "block", "unblock", "done", "fail", "cancel"])
    trssot.add_argument("--job-id", required=True)
    trssot.add_argument("--reason", default=None)
    trssot.add_argument("--evidence", default=None)
    trssot.add_argument("--meta-json", default=None, help="Optional JSON object string.")

    ssot = sub.add_parser("enqueue-ssot", help="Append an enqueue event to the SSOT branch (human only).")
    ssot.add_argument("--ssot-branch", default=DEFAULT_SSOT_BRANCH)
    ssot.add_argument("--remote", default=DEFAULT_REMOTE)
    ssot.add_argument("--actor", default=os.getenv("GITHUB_ACTOR", ""), help="Human actor (required).")
    ssot.add_argument("--kind", required=True, choices=["open_pr", "release", "changelog", "maintenance"])
    ssot.add_argument("--repo", required=True, help="owner/name")
    ssot.add_argument("--base", required=True, help="base branch, e.g. main")
    ssot.add_argument(
        "--payload-json",
        help=(
            "JSON object string (must be a dict). "
            "Example: '{\"title\":\"...\"}'. "
            "NOTE: for --kind open_pr, payload.head is required (e.g. '{\"head\":\"feature/xxx\"}')."
        ),
        required=True,
    )

    return p.parse_args()


def _load_payload(payload_json: str) -> Dict[str, Any]:
    try:
        obj = json.loads(payload_json)
    except json.JSONDecodeError as e:
        raise SchemaError(f"payload_json_invalid: {e}") from e
    if not isinstance(obj, dict):
        raise SchemaError("payload_json_must_be_object")
    return obj


def _load_meta(meta_json: str | None) -> Dict[str, Any] | None:
    if not meta_json:
        return None
    try:
        obj = json.loads(meta_json)
    except json.JSONDecodeError as e:
        raise SchemaError(f"meta_json_invalid: {e}") from e
    if not isinstance(obj, dict):
        raise SchemaError("meta_json_must_be_object")
    return obj


def _git(args: list[str]) -> str:
    r = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise WorkQueueError(f"git_failed args={' '.join(args)} stderr={r.stderr.strip()}")
    return r.stdout.strip()


def _current_branch() -> str:
    # Returns current branch name; if detached, returns 'HEAD'
    return _git(["rev-parse", "--abbrev-ref", "HEAD"]) or "HEAD"


def _switch_back(branch: str) -> None:
    if branch == "HEAD":
        subprocess.run(["git", "switch", "-"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    subprocess.run(["git", "switch", branch], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _ensure_queue_init(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"type":"__init__","note":"SSOT file placeholder; events start below"}\n')


def main() -> None:
    args = _parse_args()

    if args.cmd == "enqueue":
        actor = (args.actor or "").strip()
        if not actor:
            print("[WorkQueue] exit=4 reason=missing_actor", file=sys.stderr)
            raise SystemExit(4)

        if actor == BOT_ACTOR:
            print("[WorkQueue] exit=4 reason=human_only actor=github-actions[bot]", file=sys.stderr)
            raise SystemExit(4)

        payload = _load_payload(args.payload_json)

        if args.kind == "open_pr":
            head_ref = (payload.get("head") or "").strip() if isinstance(payload.get("head"), str) else ""
            if not head_ref:
                print("[WorkQueue] exit=4 reason=missing_payload_head kind=open_pr", file=sys.stderr)
                raise SystemExit(4)

        try:
            ev = enqueue(
                queue_path=args.queue_path,
                actor=actor,
                job_kind=args.kind,
                repo=args.repo,
                base=args.base,
                payload=payload,
            )
        except HumanOnlyViolation as e:
            print(f"[WorkQueue] exit=4 reason=human_only detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except (SchemaError, InvariantViolation) as e:
            print(f"[WorkQueue] exit=4 reason=invariant_or_schema detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except WorkQueueError as e:
            msg = str(e)
            if "git_failed" in msg:
                print(f"[WorkQueue] exit=4 reason=git_error detail={msg}", file=sys.stderr)
                raise SystemExit(4)
            print(f"[WorkQueue] exit=4 reason=work_queue_error detail={e}", file=sys.stderr)
            raise SystemExit(4)

        print(
            f"[WorkQueue] enqueue ok jobId={ev['jobId']} eventId={ev['eventId']} repo={ev['job']['repo']} base={ev['job']['base']}"
        )
        return

    if args.cmd == "transition":
        actor = (args.actor or "").strip()
        if not actor:
            print("[WorkQueue] exit=4 reason=missing_actor", file=sys.stderr)
            raise SystemExit(4)

        meta = _load_meta(args.meta_json)

        try:
            ev = append_transition(
                queue_path=args.queue_path,
                actor=actor,
                event_type=args.type,
                job_id=args.job_id,
                reason=args.reason,
                evidence=args.evidence,
                meta=meta,
            )
        except BlockedHead as e:
            print(f"[WorkQueue] exit=2 reason=blocked detail={e}", file=sys.stderr)
            raise SystemExit(2)
        except HumanOnlyViolation as e:
            print(f"[WorkQueue] exit=4 reason=human_only detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except (SchemaError, InvariantViolation) as e:
            print(f"[WorkQueue] exit=4 reason=invariant_or_schema detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except WorkQueueError as e:
            msg = str(e)
            if "git_failed" in msg:
                print(f"[WorkQueue] exit=4 reason=git_error detail={msg}", file=sys.stderr)
                raise SystemExit(4)
            print(f"[WorkQueue] exit=4 reason=work_queue_error detail={e}", file=sys.stderr)
            raise SystemExit(4)

        print(f"[WorkQueue] transition ok type={ev['type']} jobId={ev['jobId']} eventId={ev['eventId']}")
        return

    if args.cmd == "transition-ssot":
        actor = (args.actor or "").strip()
        if not actor:
            print("[WorkQueue] exit=4 reason=missing_actor", file=sys.stderr)
            raise SystemExit(4)

        meta = _load_meta(args.meta_json)

        orig = _current_branch()
        try:
            _git(["fetch", args.remote, args.ssot_branch])
            _git(["switch", "-C", "__wq__/ssot", "FETCH_HEAD"])  # local scratch branch

            _ensure_queue_init(DEFAULT_QUEUE_PATH)

            ev = append_transition(
                queue_path=DEFAULT_QUEUE_PATH,
                actor=actor,
                event_type=args.type,
                job_id=args.job_id,
                reason=args.reason,
                evidence=args.evidence,
                meta=meta,
            )

            _git(["add", DEFAULT_QUEUE_PATH])
            _git(["commit", "-m", f"chore(queue): {ev['type']} {ev['jobId']}"])
            _git(["push", args.remote, f"HEAD:{args.ssot_branch}"])

        except BlockedHead as e:
            print(f"[WorkQueue] exit=2 reason=blocked detail={e}", file=sys.stderr)
            raise SystemExit(2)
        except HumanOnlyViolation as e:
            print(f"[WorkQueue] exit=4 reason=human_only detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except (SchemaError, InvariantViolation) as e:
            print(f"[WorkQueue] exit=4 reason=invariant_or_schema detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except WorkQueueError as e:
            msg = str(e)
            if "git_failed" in msg:
                print(f"[WorkQueue] exit=4 reason=git_error detail={msg}", file=sys.stderr)
                raise SystemExit(4)
            print(f"[WorkQueue] exit=4 reason=work_queue_error detail={e}", file=sys.stderr)
            raise SystemExit(4)
        finally:
            _switch_back(orig)

        print(
            f"[WorkQueue] transition ok type={ev['type']} jobId={ev['jobId']} eventId={ev['eventId']} ssot_branch={args.ssot_branch}"
        )
        return

    if args.cmd == "enqueue-ssot":
        actor = (args.actor or "").strip()
        if not actor:
            print("[WorkQueue] exit=4 reason=missing_actor", file=sys.stderr)
            raise SystemExit(4)

        if actor == BOT_ACTOR:
            print("[WorkQueue] exit=4 reason=human_only actor=github-actions[bot]", file=sys.stderr)
            raise SystemExit(4)

        payload = _load_payload(args.payload_json)

        if args.kind == "open_pr":
            head_ref = (payload.get("head") or "").strip() if isinstance(payload.get("head"), str) else ""
            if not head_ref:
                print("[WorkQueue] exit=4 reason=missing_payload_head kind=open_pr", file=sys.stderr)
                raise SystemExit(4)

        orig = _current_branch()
        try:
            _git(["fetch", args.remote, args.ssot_branch])
            _git(["switch", "-C", "__wq__/ssot", "FETCH_HEAD"])  # local scratch branch

            _ensure_queue_init(DEFAULT_QUEUE_PATH)

            ev = enqueue(
                queue_path=DEFAULT_QUEUE_PATH,
                actor=actor,
                job_kind=args.kind,
                repo=args.repo,
                base=args.base,
                payload=payload,
            )

            _git(["add", DEFAULT_QUEUE_PATH])
            _git(["commit", "-m", f"chore(queue): enqueue {ev['jobId']}"])
            _git(["push", args.remote, f"HEAD:{args.ssot_branch}"])

        except HumanOnlyViolation as e:
            print(f"[WorkQueue] exit=4 reason=human_only detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except (SchemaError, InvariantViolation) as e:
            print(f"[WorkQueue] exit=4 reason=invariant_or_schema detail={e}", file=sys.stderr)
            raise SystemExit(4)
        except WorkQueueError as e:
            msg = str(e)
            if "git_failed" in msg:
                print(f"[WorkQueue] exit=4 reason=git_error detail={msg}", file=sys.stderr)
                raise SystemExit(4)
            print(f"[WorkQueue] exit=4 reason=work_queue_error detail={e}", file=sys.stderr)
            raise SystemExit(4)
        finally:
            _switch_back(orig)

        print(
            f"[WorkQueue] enqueue ok jobId={ev['jobId']} eventId={ev['eventId']} repo={ev['job']['repo']} base={ev['job']['base']} ssot_branch={args.ssot_branch}"
        )
        return

    raise SystemExit(1)


if __name__ == "__main__":
    main()