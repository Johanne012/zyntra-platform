"""ZYNTRA Data Science Team — Supervisor-led multi-agent service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Future: init DB / load models / warm supervisor
    yield


app = FastAPI(
    title="ZYNTRA Data Science Team",
    version=__version__,
    description="Supervisor-led multi-agent Data Science service integrated into ZYNTRA Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):  # type: ignore[no-untyped-def]
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "zyntra-data-science-team",
        "version": __version__,
    }


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "ZYNTRA Data Science Team",
        "docs": "/docs",
        "health": "/health",
    }
