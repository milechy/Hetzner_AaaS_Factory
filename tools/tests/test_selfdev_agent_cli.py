import json
import sys

import tools.selfdev_agent_cli as cli


def test_selfdev_agent_cli_outputs_proposal(capsys, monkeypatch):
    brief = {"task_id": "selfdev-v4-cli-001", "goal": "Add CLI entrypoint"}
    monkeypatch.setattr(
        sys,
        "argv",
        ["selfdev_agent_cli", "--brief-json", json.dumps(brief)],
    )

    cli.main()
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)

    for key in ("summary", "risk_level", "task_kind"):
        assert key in payload
    for key in ("context_scan", "plan", "reflection"):
        assert key in payload
    assert isinstance(payload.get("context_scan"), dict)
    assert isinstance(payload.get("plan"), dict)
    assert isinstance(payload.get("plan", {}).get("steps"), list)
    assert isinstance(payload.get("reflection"), list)

    assert isinstance(payload.get("router_proofs"), list)
    assert isinstance(payload.get("review_result"), dict)
    for key in ("status", "summary", "checks", "violations", "open_questions"):
        assert key in payload["review_result"]
