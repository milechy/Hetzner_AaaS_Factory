from apps.agents.selfdev_agent.router_client import LLMRouterClient, RouterRequiredError
from apps.agents.selfdev_agent.selfdev_agent_v4 import PermissionDeniedError, ToolPermissions, SelfDevAgentV4
from apps.agents.selfdev_agent.schemas import PRProposal, TaskBrief


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
    assert isinstance(d["invariant_findings"], list)
    for finding in d["invariant_findings"]:
        assert "code" in finding
        assert "severity" in finding
        assert "message" in finding
        assert finding["severity"] in {"warn", "fix_required"}
    fix_required = [
        finding for finding in d["invariant_findings"] if finding["severity"] == "fix_required"
    ]
    assert fix_required == []
    assert isinstance(d["context_scan"], dict)
    assert d["context_scan"]["task_id"] == brief.task_id
    assert d["context_scan"]["goal"]
    assert isinstance(d["plan"], dict)
    assert isinstance(d["plan"]["steps"], list)
    assert len(d["plan"]["steps"]) >= 1
    assert all(step.get("step") for step in d["plan"]["steps"])
    assert isinstance(d["reflection"], list)
    assert len(d["reflection"]) >= 2
    assert "note" in d["reflection"][0]
    assert ("review" in d["reflection"][0]["note"].lower()) or ("note(s)" in d["reflection"][0]["note"])
    assert "router_proofs" in d
    assert isinstance(d["router_proofs"], list)
    assert len(d["router_proofs"]) >= 2
    profiles = {proof.get("profile") for proof in d["router_proofs"]}
    assert "writer" in profiles
    assert "reviewer" in profiles
    for proof in d["router_proofs"]:
        assert "profile" in proof
        assert "selected_model" in proof
        assert proof.get("rationale")
        assert isinstance(proof.get("fallback_chain"), list)
        assert len(proof.get("fallback_chain")) >= 1
        if proof.get("profile") == "reviewer":
            assert proof.get("task_kind") == "review"
    assert isinstance(d["verification"], dict)
    for key in ("tests", "lint", "format"):
        assert key in d["verification"]
        assert isinstance(d["verification"][key], dict)
        assert "status" in d["verification"][key]
        assert "command" in d["verification"][key]
    assert isinstance(d["validation"], dict)
    for key in (
        "invariants_ok",
        "violations",
        "warnings",
        "fix_required_questions",
        "checked_items",
    ):
        assert key in d["validation"]
    assert d["validation"]["invariants_ok"] is True


def test_validation_fails_for_broken_proposal():
    agent = SelfDevAgentV4(router=LLMRouterClient())
    brief = TaskBrief(task_id="selfdev-v4-mvp-002", goal="Validate failure case")
    proposal = PRProposal(
        summary="Broken proposal",
        risk_level="low",
        task_kind="implement",
        router_proofs=[],
        context_scan=None,
        plan=None,
    )
    validation = agent.validate_proposal_invariants(proposal, brief)
    assert validation.invariants_ok is False
    assert validation.violations
