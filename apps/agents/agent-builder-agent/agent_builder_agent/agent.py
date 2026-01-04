from __future__ import annotations

import os

from agents import Agent  # provided by openai-agents  [oai_citation:2‡オープンAIクックブック](https://cookbook.openai.com/examples/build_a_coding_agent_with_gpt-5.1)

from agent_builder_agent.core.errors import error_response
from agent_builder_agent.core.proposal_builder import build_pull_request_proposal
from agent_builder_agent.core.risk_detector import detect_high_risk
from agent_builder_agent.core.skeleton_generator import generate_skeleton, infer_steps_if_missing
from agent_builder_agent.core.spec_parser import SpecParseError, normalize_spec, parse_spec
from agent_builder_agent.router.llm_router_client import LLMRouterClient, LLMRouterConfig, LLMRouterError
from agent_builder_agent.schemas.agent_builder_request_v0 import AgentBuilderRequestV0


def build_agent() -> Agent:
    """
    OpenAI Agents SDK Agent wrapper.
    This agent exposes one "function-like" behavior via your application integration:
      - feed it a JSON request; it returns PullRequestProposal JSON or Error JSON.

    NOTE: We keep orchestration minimal; most apps will call AgentBuilderAgentV0.build_proposal() directly.
    """
    return Agent(
        name="AgentBuilderAgentV0",
        instructions=(
            "You are AgentBuilderAgent v0. You only produce PullRequestProposal(JSON) "
            "or AgentBuilderError(JSON). You do not perform git/infra/secret operations."
        ),
        tools=[],
    )


class AgentBuilderAgentV0:
    def __init__(self, router: LLMRouterClient) -> None:
        self._router = router

    @staticmethod
    def _router_from_env() -> LLMRouterClient:
        base_url = os.environ.get("LLM_ROUTER_URL", "").strip()
        if not base_url:
            raise RuntimeError("LLM_ROUTER_URL is required to run AgentBuilderAgentV0.")
        api_key = os.environ.get("LLM_ROUTER_API_KEY")
        return LLMRouterClient(LLMRouterConfig(base_url=base_url, api_key=api_key))

    @classmethod
    def from_env(cls) -> "AgentBuilderAgentV0":
        return cls(router=cls._router_from_env())

    async def build_proposal(self, request_json: dict) -> dict:
        # 1) validate request contract
        try:
            req = AgentBuilderRequestV0.model_validate(request_json)
        except Exception as e:
            request_id = str(request_json.get("requestId", "unknown"))
            return error_response(
                request_id=request_id,
                code="SPEC_VALIDATION_FAILED",
                message="Request validation failed.",
                details=[str(e)],
            )

        # 2) parse spec
        spec_text, spec_obj = req.get_spec_payload()
        try:
            raw = parse_spec(spec_format=req.specFormat, spec_text=spec_text, spec_obj=spec_obj)
            parsed = normalize_spec(raw)  # enforces name/purpose; steps optional
        except SpecParseError as e:
            return error_response(
                request_id=req.requestId,
                code="SPEC_PARSE_FAILED",
                message="Failed to parse spec.",
                details=[str(e)],
            )

        # 3) risk detect (high-risk => omit files, but still propose skeleton)
        risk = detect_high_risk(parsed.raw)

        # 4) infer steps if missing (agreed behavior: steps are optional)
        try:
            steps = await infer_steps_if_missing(
                router=self._router,
                routing_profile=req.routingProfile,
                name=parsed.name,
                purpose=parsed.purpose,
                raw_spec=parsed.raw,
                existing_steps=parsed.steps,
            )
        except (LLMRouterError, Exception) as e:
            # If router fails, fallback to a minimal default step list
            steps = ["Define project structure", "Generate core modules", "Add minimal README"]

        # 5) generate skeleton (must omit high-risk files)
        try:
            sk = await generate_skeleton(
                router=self._router,
                routing_profile=req.routingProfile,
                target=req.target.model_dump(mode="json"),
                spec=parsed.raw,
                steps=steps,
            )
        except Exception as e:
            return error_response(
                request_id=req.requestId,
                code="INTERNAL_ERROR",
                message="Failed to generate skeleton.",
                details=[str(e)],
            )

        # 6) build proposal
        title = f"Scaffold {parsed.name} skeleton (proposal-only)"
        summary = (
            f"Generates a minimal skeleton for '{parsed.name}' based on the provided spec. "
            f"Outputs are proposal-only; no git/infra/secret operations are performed. "
            f"Steps were {'inferred' if not parsed.steps else 'provided'}.\n\n"
            f"Purpose: {parsed.purpose}"
        )

        files = [(f.path, f.content_type, f.content) for f in sk.files]

        proposal = build_pull_request_proposal(
            request_id=req.requestId,
            router_profile=req.routingProfile,
            title=title,
            summary=summary,
            risk=risk,
            directories=sk.directories,
            files=files,
            dependencies=[],
        )
        return proposal.model_dump(mode="json")