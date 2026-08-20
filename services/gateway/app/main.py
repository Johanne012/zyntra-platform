"""ZYNTRA Gateway — secured entrypoint with monitoring."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.balancer import ProviderBalancer
from app.config import Settings, get_settings
from app.pricing import calc_cost_usd
from app.providers import Provider, build_providers, chat_completion, resolve_model
from app.security import RateLimiter, SecurityHeadersMiddleware, client_ip, parse_cors_origins, require_gateway_key
from app.stats import stats


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = "gpt-4o-mini"
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    provider: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.gateway_environment == "production" and not settings.gateway_api_key:
        raise RuntimeError("GATEWAY_API_KEY must be set in production")
    app.state.settings = settings
    app.state.http = httpx.AsyncClient()
    app.state.providers = build_providers(settings)
    app.state.balancer = ProviderBalancer(settings.gateway_balance_strategy)
    app.state.rate_limiter = RateLimiter(settings.gateway_rate_limit_per_minute, 60)
    yield
    await app.state.http.aclose()


app = FastAPI(title="ZYNTRA Gateway", version="0.3.1", lifespan=lifespan)
_settings_boot = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=parse_cors_origins(_settings_boot.gateway_cors_origins), allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "X-API-Key"])
app.add_middleware(SecurityHeadersMiddleware)


def _auth(authorization: Annotated[str | None, Header()] = None, x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None) -> None:
    require_gateway_key(getattr(app.state, "settings", None) or get_settings(), authorization, x_api_key)


def _rate_limit(request: Request) -> None:
    limiter: RateLimiter | None = getattr(app.state, "rate_limiter", None)
    if limiter is not None:
        limiter.check(client_ip(request))


@app.get("/health")
async def health() -> dict[str, Any]:
    settings: Settings = getattr(app.state, "settings", None) or get_settings()
    providers: list[Provider] = getattr(app.state, "providers", None) or []
    return {
        "status": "ok",
        "service": "zyntra-gateway",
        "version": "0.3.1",
        "environment": settings.gateway_environment,
        "auth_required": bool(settings.gateway_api_key) or settings.gateway_environment == "production",
        "balance_strategy": settings.gateway_balance_strategy,
        "providers": [{"id": p.id, "configured": p.configured, "in_cooldown": stats.is_in_cooldown(p.id)} for p in providers],
    }


@app.get("/v1/stats")
async def usage_stats(_: Annotated[None, Depends(_auth)] = None) -> dict[str, Any]:
    return stats.snapshot()


@app.get("/v1/models")
async def list_models(_: Annotated[None, Depends(_auth)] = None) -> dict[str, Any]:
    providers: list[Provider] = getattr(app.state, "providers", None) or []
    data = [{"id": f"{p.id}/{alias}", "object": "model", "owned_by": p.id} for p in providers if p.configured for alias in sorted(set(p.model_map.values()))]
    return {"object": "list", "data": data}


def _select_providers(req_provider: str | None) -> list[Provider]:
    providers: list[Provider] = getattr(app.state, "providers", None) or []
    by_id = {p.id: p for p in providers if p.configured}
    if req_provider:
        if req_provider not in by_id:
            raise HTTPException(status_code=400, detail=f"Provider not configured: {req_provider}")
        return [by_id[req_provider]]
    if not by_id:
        raise HTTPException(status_code=503, detail="No providers configured")
    ids = [p.id for p in providers if p.configured and not stats.is_in_cooldown(p.id)] or list(by_id)
    balancer: ProviderBalancer = getattr(app.state, "balancer", None) or ProviderBalancer("round_robin")
    weights = {p.id: p.weight for p in providers}
    return [by_id[i] for i in balancer.order(ids, weights=weights) if i in by_id]


def _extract_usage(data: dict) -> tuple[int, int]:
    usage = data.get("usage") or {}
    return int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)


@app.post("/v1/chat/completions")
async def completions(body: ChatRequest, request: Request, _: Annotated[None, Depends(_auth)] = None, __: Annotated[None, Depends(_rate_limit)] = None) -> Any:
    settings: Settings = getattr(app.state, "settings", None) or get_settings()
    client: httpx.AsyncClient | None = getattr(app.state, "http", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Gateway not ready")
    errors: list[str] = []
    for provider in _select_providers(body.provider):
        model = resolve_model(provider, body.model)
        started = time.perf_counter()
        try:
            resp = await chat_completion(client, provider, model=model, messages=[m.model_dump() for m in body.messages], stream=body.stream, temperature=body.temperature, max_tokens=body.max_tokens)
        except httpx.HTTPError as exc:
            latency = (time.perf_counter() - started) * 1000
            stats.record_failure(provider.id, str(exc), latency_ms=latency)
            errors.append(f"{provider.id}: {exc}")
            continue
        latency = (time.perf_counter() - started) * 1000
        if resp.status_code >= 400:
            text = resp.text[:200]
            stats.record_failure(provider.id, f"HTTP {resp.status_code} {text}", is_rate_limit=resp.status_code == 429, latency_ms=latency)
            await resp.aclose()
            errors.append(f"{provider.id}: HTTP {resp.status_code} {text}")
            continue
        if body.stream:
            async def event_stream(r: httpx.Response = resp) -> AsyncIterator[bytes]:
                try:
                    async for chunk in r.aiter_bytes():
                        yield chunk
                finally:
                    await r.aclose()
            stats.record_success(provider.id, latency_ms=latency)
            return StreamingResponse(event_stream(), media_type="text/event-stream")
        try:
            data = resp.json()
        finally:
            await resp.aclose()
        in_tok, out_tok = _extract_usage(data) if isinstance(data, dict) else (0, 0)
        cost = calc_cost_usd(model, in_tok, out_tok)
        if isinstance(data, dict):
            data.setdefault("zyntra", {}).update(provider=provider.id, model=model, cost_usd=cost, latency_ms=round(latency, 2))
        stats.record_success(provider.id, input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost, latency_ms=latency)
        return JSONResponse(data)
    raise HTTPException(status_code=502, detail={"message": "All providers failed", "errors": errors, "default_provider": settings.gateway_default_provider})
