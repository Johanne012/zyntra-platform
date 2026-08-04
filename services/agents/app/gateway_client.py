"""Call internal ZYNTRA Gateway for LLM completions."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


async def chat(
    messages: list[dict[str, str]],
    *,
    model: str = "gpt-4o-mini",
    temperature: float | None = 0.2,
) -> str:
    settings = get_settings()
    url = f"{settings.gateway_internal_url.rstrip('/')}/v1/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if temperature is not None:
        payload["temperature"] = temperature

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if settings.gateway_api_key_internal:
        headers["Authorization"] = f"Bearer {settings.gateway_api_key_internal}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected gateway response: {data}") from exc
