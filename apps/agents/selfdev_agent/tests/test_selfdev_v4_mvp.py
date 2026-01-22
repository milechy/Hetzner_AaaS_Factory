from apps.agents.selfdev_agent.router_client import LLMRouterClient, RouterRequiredError
from apps.agents.selfdev_agent.selfdev_agent_v4 import PermissionDeniedError, ToolPermissions, SelfDevAgentV4
from apps.agents.selfdev_agent.schemas import TaskBrief


def test_router_requires_profile():
    r = LLMRouterClient()
    try:
        r.route(profile="invalid", risk_level="low", task_kind="review")
        raise AssertionError("expected RouterRequiredError")
    except RouterRequiredError:
        pass


def test_reviewer_cannot_write_or_run():
    perms = ToolPermissions(profile="reviewer")
    try:
        perms.assert_can_write()
        raise AssertionError("expected PermissionDeniedError")
    except PermissionDeniedError:
        pass
    try:
        perms.assert_can_run()
        raise AssertionError("expected PermissionDeniedError")
    except PermissionDeniedError:
        pass


def test_agent_run_returns_proposal():
    agent = SelfDevAgentV4(router=LLMRouterClient())
    brief = TaskBrief(task_id="selfdev-v4-mvp-001", goal="Implement MVP skeleton")
    proposal = agent.run(brief)
    d = proposal.to_dict()
    assert d["risk_level"] in ("low", "medium", "high")
    assert "summary" in d
    assert isinstance(d["review_notes"], list)
    assert d["open_questions"] == []
    assert any("PASS" in note for note in d["review_notes"])
    assert isinstance(d["context_scan"], dict)
    assert d["context_scan"]["task_id"] == brief.task_id
    assert isinstance(d["plan"], dict)
    assert isinstance(d["plan"]["steps"], list)
    assert 1 <= len(d["plan"]["steps"]) <= 3
    assert isinstance(d["reflection"], list)
    assert "router_proofs" in d
    assert isinstance(d["router_proofs"], list)
    assert len(d["router_proofs"]) >= 2
    for proof in d["router_proofs"]:
        assert "profile" in proof
        assert "selected_model" in proof
    assert isinstance(d["verification"], dict)
    for key in ("tests", "lint", "format"):
        assert key in d["verification"]
        assert isinstance(d["verification"][key], dict)
        assert "status" in d["verification"][key]
        assert "command" in d["verification"][key]
