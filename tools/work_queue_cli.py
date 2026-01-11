# tools/work_queue_cli.py
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

from tools.work_queue import (
    BOT_ACTOR,
    HumanOnlyViolation,
    InvariantViolation,
    SchemaError,
    WorkQueueError,
    enqueue,
)

DEFAULT_QUEUE_PATH = "factory/work_queue.jsonl"


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
        required=True,
        help="JSON object string (must be a dict). Example: '{\"title\":\"...\"}'",
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
            print(f"[WorkQueue] exit=4 reason=work_queue_error detail={e}", file=sys.stderr)
            raise SystemExit(4)

        print(
            f"[WorkQueue] enqueue ok jobId={ev['jobId']} eventId={ev['eventId']} repo={ev['job']['repo']} base={ev['job']['base']}"
        )
        return

    raise SystemExit(1)


if __name__ == "__main__":
    main()