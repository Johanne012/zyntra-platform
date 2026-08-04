"""ZYNTRA Gateway — FastAPI entrypoint with lifespan, balancer, stats."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.balancer import ProviderBalancer
from app.config import Settings, get_settings
from app.pricing import calc_cost_usd
from app.providers import Provider, build_providers, chat_completion, resolve_model
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
    app.state.settings = settings
    app.state.http = httpx.AsyncClient()
    app.state.providers = build_providers(settings)
    app.state.balancer = ProviderBalancer(settings.gateway_balance_strategy)
    yield
    await app.state.http.aclose()


app = FastAPI(
    title="ZYNTRA Gateway",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    providers: list[Provider] = app.state.providers
    return {
        "status": "ok",
        "service": "zyntra-gateway",
        "version": "0.2.0",
        "balance_strategy": app.state.settings.gateway_balance_strategy,
        "providers": [
            {
                "id": p.id,
                "available": p.available,
                "in_cooldown": stats.is_in_cooldown(p.id),
            }
            for p in providers
        ],
    }


@app.get("/v1/stats")
async def usage_stats() -> dict[str, Any]:
    return stats.snapshot()


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    providers: list[Provider] = app.state.providers
    data = []
    for p in providers:
        if not p.available:
            continue
        for alias in sorted(set(p.model_map.values())):
            data.append({"id": f"{p.id}/{alias}", "object": "model", "owned_by": p.id})
    return {"object": "list", "data": data}


def _select_providers(req_provider: str | None) -> list[Provider]:
    providers: list[Provider] = app.state.providers
    by_id = {p.id: p for p in providers if p.available}
    if req_provider:
        if req_provider not in by_id:
            raise HTTPException(status_code=400, detail=f"Provider not available: {req_provider}")
        return [by_id[req_provider]]
    if not by_id:
        raise HTTPException(
            status_code=503,
            detail="No providers configured. Set at least one API key in the environment.",
        )

    ids = [p.id for p in providers if p.available and not stats.is_in_cooldown(p.id)]
    if not ids:
        ids = list(by_id.keys())

    balancer: ProviderBalancer = app.state.balancer
    weights = {p.id: p.weight for p in providers}
    ordered_ids = balancer.order(ids, weights=weights)
    return [by_id[i] for i in ordered_ids if i in by_id]


def _extract_usage(data: dict) -> tuple[int, int]:
    usage = data.get("usage") or {}
    return int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)


@app.post("/v1/chat/completions")
async def completions(body: ChatRequest) -> Any:
    settings: Settings = app.state.settings
    client: httpx.AsyncClient = app.state.http
    chain = _select_providers(body.provider)
    messages = [m.model_dump() for m in body.messages]
    errors: list[str] = []

    for provider in chain:
        model = resolve_model(provider, body.model)
        try:
            resp = await chat_completion(
                client,
                provider,
                model=model,
                messages=messages,
                stream=body.stream,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            )
        except httpx.HTTPError as exc:
            msg = str(exc)
            stats.record_failure(provider.id, msg)
            errors.append(f"{provider.id}: {msg}")
            continue

        if resp.status_code >= 400:
            text = resp.text[:200]
            is_rl = resp.status_code == 429
            stats.record_failure(
                provider.id, f"HTTP {resp.status_code} {text}", is_rate_limit=is_rl
            )
            errors.append(f"{provider.id}: HTTP {resp.status_code} {text}")
            continue

        if body.stream:
            stream_resp = resp

            async def event_stream(
                r: httpx.Response = stream_resp,
            ) -> AsyncIterator[bytes]:
                async for chunk in r.aiter_bytes():
                    yield chunk

            stats.record_success(provider.id)
            return StreamingResponse(event_stream(), media_type="text/event-stream")

        data = resp.json()
        in_tok, out_tok = (0, 0)
        cost = 0.0
        if isinstance(data, dict):
            in_tok, out_tok = _extract_usage(data)
            cost = calc_cost_usd(model, in_tok, out_tok)
            data.setdefault("zyntra", {})["provider"] = provider.id
            data.setdefault("zyntra", {})["model"] = model
            data.setdefault("zyntra", {})["cost_usd"] = cost
        stats.record_success(
            provider.id, input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost
        )
        return JSONResponse(data)

    raise HTTPException(
        status_code=502,
        detail={
            "message": "All providers failed",
            "errors": errors,
            "default_provider": settings.gateway_default_provider,
            "balance_strategy": settings.gateway_balance_strategy,
        },
    )
