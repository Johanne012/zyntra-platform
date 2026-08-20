"""Provider registry — ordered fallback across configured backends."""

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
    weight: int = 1

    @property
    def configured(self) -> bool:
        # Ollama needs no API key, but configured does not mean reachable.
        return self.id == "ollama" or bool(self.api_key)

    @property
    def available(self) -> bool:
        """Backward-compatible alias: means configured, not network-healthy."""
        return self.configured


def build_providers(settings: Settings) -> list[Provider]:
    providers = [
        Provider("deepseek", "https://api.deepseek.com", settings.deepseek_api_key, {"default": "deepseek-chat", "gpt-4o-mini": "deepseek-chat", "gpt-4o": "deepseek-chat"}, 3),
        Provider("openrouter", "https://openrouter.ai/api/v1", settings.openrouter_api_key, {"default": "openai/gpt-4o-mini", "gpt-4o-mini": "openai/gpt-4o-mini", "gpt-4o": "openai/gpt-4o"}, 2),
        Provider("groq", "https://api.groq.com/openai/v1", settings.groq_api_key, {"default": "llama-3.1-8b-instant", "gpt-4o-mini": "llama-3.1-8b-instant", "gpt-4o": "llama-3.3-70b-versatile"}, 2),
        Provider("nvidia_nim", "https://integrate.api.nvidia.com/v1", settings.nvidia_nim_api_key, {"default": "meta/llama-3.1-8b-instruct", "gpt-4o-mini": "meta/llama-3.1-8b-instruct"}),
        Provider("kimi", "https://api.moonshot.cn/v1", settings.kimi_api_key, {"default": "moonshot-v1-8k", "gpt-4o-mini": "moonshot-v1-8k"}),
        Provider("ollama", f"{settings.ollama_base_url.rstrip('/')}/v1", "ollama", {"default": "llama3.2", "gpt-4o-mini": "llama3.2"}),
    ]
    default = settings.gateway_default_provider
    providers.sort(key=lambda p: (0 if p.id == default else 1, p.id))
    return providers


def resolve_model(provider: Provider, requested: str | None) -> str:
    return provider.model_map.get(requested or "default", provider.model_map["default"])


async def chat_completion(client: httpx.AsyncClient, provider: Provider, *, model: str, messages: list[dict], stream: bool, temperature: float | None = None, max_tokens: int | None = None) -> httpx.Response:
    headers = {"Content-Type": "application/json"}
    if provider.api_key and provider.id != "ollama":
        headers["Authorization"] = f"Bearer {provider.api_key}"
    body: dict = {"model": model, "messages": messages, "stream": stream}
    if temperature is not None:
        body["temperature"] = temperature
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    return await client.post(f"{provider.base_url}/chat/completions", headers=headers, json=body, timeout=120.0)
