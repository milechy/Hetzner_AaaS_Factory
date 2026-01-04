from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


class LLMRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMRouterConfig:
    base_url: str
    timeout_seconds: float = 60.0
    api_key: Optional[str] = None  # if your router requires auth


class LLMRouterClient:
    """
    Contract:
      - caller provides profile only
      - router decides model
      - response returns { "text": "...", "meta": {...} }
    """

    def __init__(self, config: LLMRouterConfig) -> None:
        self._config = config

    async def complete(self, *, profile: str, input_text: str, context: Optional[dict[str, Any]] = None) -> str:
        url = f"{self._config.base_url.rstrip('/')}/v1/complete"
        headers = {"content-type": "application/json"}
        if self._config.api_key:
            headers["authorization"] = f"Bearer {self._config.api_key}"

        payload = {
            "profile": profile,
            "input": input_text,
            "context": context or {},
        }

        async with httpx.AsyncClient(timeout=self._config.timeout_seconds) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                raise LLMRouterError(f"LLMRouter error: {resp.status_code} {resp.text}")

            data = resp.json()
            text = data.get("text")
            if not isinstance(text, str) or not text.strip():
                raise LLMRouterError("LLMRouter returned empty text")
            return text