"""Client for ZYNTRA Gateway (OpenAI-compatible)."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


async def chat(
    messages: list[dict[str, str]],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    api_key: str | None = None,
) -> str:
    """Call the ZYNTRA gateway chat completions endpoint."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    url = f"{settings.gateway_internal_url.rstrip('/')}/v1/chat/completions"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected gateway response: {data}") from exc
