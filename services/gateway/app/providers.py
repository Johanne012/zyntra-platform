"""Provider registry — ordered fallback across free/cheap backends."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import Settings


@dataclass(frozen=True)
class Provider:
    id: str
    base_url: str
    api_key: str | None
    model_map: dict[str, str]

    @property
    def available(self) -> bool:
        # Ollama needs no key; others need a non-empty key
        if self.id == "ollama":
            return True
        return bool(self.api_key)


def build_providers(settings: Settings) -> list[Provider]:
    providers = [
        Provider(
            id="deepseek",
            base_url="https://api.deepseek.com",
            api_key=settings.deepseek_api_key,
            model_map={
                "default": "deepseek-chat",
                "gpt-4o-mini": "deepseek-chat",
                "gpt-4o": "deepseek-chat",
            },
        ),
        Provider(
            id="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            model_map={
                "default": "openai/gpt-4o-mini",
                "gpt-4o-mini": "openai/gpt-4o-mini",
                "gpt-4o": "openai/gpt-4o",
            },
        ),
        Provider(
            id="nvidia_nim",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=settings.nvidia_nim_api_key,
            model_map={
                "default": "meta/llama-3.1-8b-instruct",
                "gpt-4o-mini": "meta/llama-3.1-8b-instruct",
            },
        ),
        Provider(
            id="kimi",
            base_url="https://api.moonshot.cn/v1",
            api_key=settings.kimi_api_key,
            model_map={
                "default": "moonshot-v1-8k",
                "gpt-4o-mini": "moonshot-v1-8k",
            },
        ),
        Provider(
            id="ollama",
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
            model_map={
                "default": "llama3.2",
                "gpt-4o-mini": "llama3.2",
            },
        ),
    ]
    # Prefer default provider first if available
    default = settings.gateway_default_provider
    providers.sort(key=lambda p: (0 if p.id == default else 1, p.id))
    return providers


def resolve_model(provider: Provider, requested: str | None) -> str:
    if not requested:
        return provider.model_map["default"]
    return provider.model_map.get(requested, provider.model_map["default"])


async def chat_completion(
    client: httpx.AsyncClient,
    provider: Provider,
    *,
    model: str,
    messages: list[dict],
    stream: bool,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> httpx.Response:
    headers = {"Content-Type": "application/json"}
    if provider.api_key and provider.id != "ollama":
        headers["Authorization"] = f"Bearer {provider.api_key}"

    body: dict = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }
    if temperature is not None:
        body["temperature"] = temperature
    if max_tokens is not None:
        body["max_tokens"] = max_tokens

    return await client.post(
        f"{provider.base_url}/chat/completions",
        headers=headers,
        json=body,
        timeout=120.0,
    )
