from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_builder_agent.core.risk_detector import is_high_risk_path
from agent_builder_agent.router.llm_router_client import LLMRouterClient


@dataclass(frozen=True)
class SkeletonFile:
    path: str
    content: str
    content_type: str  # text|python|md|json|yaml


@dataclass(frozen=True)
class SkeletonResult:
    directories: list[str]
    files: list[SkeletonFile]
    inferred_steps: list[str]


_INFER_STEPS_PROMPT = """You are AgentBuilderAgent v0.
Infer an implementation skeleton plan (steps) from the following spec.
Return a JSON array of short strings, each <= 80 chars. Do not include any infra/security/billing/template steps.

SPEC_NAME: {name}
SPEC_PURPOSE: {purpose}
SPEC_RAW: {raw}
"""

_GENERATE_SKELETON_PROMPT = """You are AgentBuilderAgent v0.
Generate a minimal, safe project skeleton for the target.
Constraints:
- proposal-only; do not include git commands
- do not create infra/security/billing/template files
- keep files minimal but runnable
Return JSON object:
{{
  "directories": ["..."],
  "files": [{{"path":"...","contentType":"python|md|json|text","content":"..."}}, ...]
}}
TARGET: {target}
STEPS: {steps}
SPEC: {spec}
"""


async def infer_steps_if_missing(
    *,
    router: LLMRouterClient,
    routing_profile: str,
    name: str,
    purpose: str,
    raw_spec: dict[str, Any],
    existing_steps: list[str],
) -> list[str]:
    if existing_steps:
        return existing_steps

    prompt = _INFER_STEPS_PROMPT.format(name=name, purpose=purpose, raw=raw_spec)
    text = await router.complete(profile=routing_profile, input_text=prompt, context={"task": "infer_steps"})
    # defensive parse: accept either JSON array or newline list
    text_s = text.strip()
    if text_s.startswith("["):
        import json

        arr = json.loads(text_s)
        if isinstance(arr, list):
            steps = [str(x).strip() for x in arr if str(x).strip()]
            return steps[:12]
    return [line.strip("- ").strip() for line in text_s.splitlines() if line.strip()][:12]


async def generate_skeleton(
    *,
    router: LLMRouterClient,
    routing_profile: str,
    target: dict[str, Any],
    spec: dict[str, Any],
    steps: list[str],
) -> SkeletonResult:
    import json

    prompt = _GENERATE_SKELETON_PROMPT.format(target=target, steps=steps, spec=spec)
    text = await router.complete(profile=routing_profile, input_text=prompt, context={"task": "generate_skeleton"})
    data = json.loads(text)

    directories = [d for d in data.get("directories", []) if isinstance(d, str)]
    files_in = data.get("files", [])
    files: list[SkeletonFile] = []
    for f in files_in:
        if not isinstance(f, dict):
            continue
        path = str(f.get("path", "")).strip()
        if not path:
            continue
        if is_high_risk_path(path):
            # v0: omit high-risk files entirely
            continue
        content = str(f.get("content", ""))
        content_type = str(f.get("contentType", "text"))
        files.append(SkeletonFile(path=path, content=content, content_type=content_type))

    # ensure at least a README exists (non-high-risk)
    if not any(x.path.lower().endswith("readme.md") for x in files):
        files.append(
            SkeletonFile(
                path="README.md",
                content=f"# {spec.get('name','Agent')}\n\n{spec.get('purpose','')}\n",
                content_type="md",
            )
        )

    return SkeletonResult(directories=directories, files=files, inferred_steps=steps)