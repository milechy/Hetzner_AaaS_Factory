from __future__ import annotations

import asyncio
import json
import sys

from agent_builder_agent.agent import AgentBuilderAgentV0


async def main() -> None:
    data = json.loads(sys.stdin.read())
    agent = AgentBuilderAgentV0.from_env()
    out = await agent.build_proposal(data)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())