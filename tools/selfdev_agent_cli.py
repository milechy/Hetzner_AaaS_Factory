from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict

from apps.agents.selfdev_agent.router_client import LLMRouterClient
from apps.agents.selfdev_agent.schemas import TaskBrief
from apps.agents.selfdev_agent.selfdev_agent_v4 import SelfDevAgentV4


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="selfdev_agent_cli")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brief-json", help="TaskBrief JSON string")
    group.add_argument("--brief-file", help="Path to TaskBrief JSON file")
    return parser.parse_args()


def _load_brief_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if args.brief_json:
        raw = args.brief_json
    else:
        path = Path(args.brief_file)
        raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"brief_json_invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("brief_json_must_be_object")
    return payload


def _brief_from_payload(payload: Dict[str, Any]) -> TaskBrief:
    if not payload.get("task_id") or not payload.get("goal"):
        raise ValueError("brief_requires_task_id_and_goal")

    list_fields = {"non_goals", "repo_scope", "definition_of_done", "constraints"}
    kwargs: Dict[str, Any] = {}
    for field in fields(TaskBrief):
        if field.name in payload:
            value = payload[field.name]
            if field.name in list_fields and value is None:
                continue
            kwargs[field.name] = value
    return TaskBrief(**kwargs)


def main() -> None:
    args = _parse_args()
    try:
        payload = _load_brief_payload(args)
        brief = _brief_from_payload(payload)
    except ValueError as exc:
        print(f"[SelfDevAgentCLI] exit=2 reason={exc}", file=sys.stderr)
        raise SystemExit(2)

    agent = SelfDevAgentV4(router=LLMRouterClient())
    proposal = agent.run(brief)
    print(json.dumps(proposal.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    main()
