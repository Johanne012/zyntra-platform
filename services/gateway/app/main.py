"""ZYNTRA Gateway — FastAPI entrypoint with lifespan."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.providers import Provider, build_providers, chat_completion, resolve_model


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = "gpt-4o-mini"
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    # Optional: force a provider id
    provider: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.http = httpx.AsyncClient()
    app.state.providers = build_providers(settings)
    yield
    await app.state.http.aclose()


app = FastAPI(
    title="ZYNTRA Gateway",
    version="0.1.0",
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
        "providers": [
            {"id": p.id, "available": p.available} for p in providers
        ],
    }


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
    available = [p for p in providers if p.available]
    if req_provider:
        matched = [p for p in available if p.id == req_provider]
        if not matched:
            raise HTTPException(status_code=400, detail=f"Provider not available: {req_provider}")
        return matched
    if not available:
        raise HTTPException(
            status_code=503,
            detail="No providers configured. Set at least one API key in the environment.",
        )
    return available


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
            errors.append(f"{provider.id}: {exc}")
            continue

        if resp.status_code >= 400:
            errors.append(f"{provider.id}: HTTP {resp.status_code} {resp.text[:200]}")
            continue

        if body.stream:

            async def event_stream() -> AsyncIterator[bytes]:
                async for chunk in resp.aiter_bytes():
                    yield chunk

            return StreamingResponse(event_stream(), media_type="text/event-stream")

        data = resp.json()
        # Tag which provider served the request
        if isinstance(data, dict):
            data.setdefault("zyntra", {})["provider"] = provider.id
            data.setdefault("zyntra", {})["model"] = model
        return JSONResponse(data)

    raise HTTPException(
        status_code=502,
        detail={
            "message": "All providers failed",
            "errors": errors,
            "default_provider": settings.gateway_default_provider,
        },
    )
