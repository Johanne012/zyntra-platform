"""ZYNTRA Data Science Team — Supervisor-led multi-agent service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app import __version__
from app.pipeline import store
from app.supervisor import Supervisor, supervisor


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
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


class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    steps: list[str] = Field(default_factory=lambda: list(Supervisor.DEFAULT_STEPS))


class PipelineOut(BaseModel):
    id: str
    name: str
    status: str
    steps: list[str]
    results: list[dict[str, Any]]
    created_at: str
    updated_at: str


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


@app.get("/v1/agents")
async def list_agents() -> list[dict[str, str]]:
    return supervisor.list_agents()


@app.post("/v1/pipelines", response_model=PipelineOut)
async def create_pipeline(body: PipelineCreate) -> dict[str, Any]:
    unknown = [s for s in body.steps if s not in supervisor.agents]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agents: {unknown}. Available: {list(supervisor.agents.keys())}",
        )
    pipe = store.create(name=body.name, steps=body.steps)
    return pipe.to_public()


@app.get("/v1/pipelines", response_model=list[PipelineOut])
async def list_pipelines() -> list[dict[str, Any]]:
    return [p.to_public() for p in store.list()]


@app.get("/v1/pipelines/{pipeline_id}", response_model=PipelineOut)
async def get_pipeline(pipeline_id: str) -> dict[str, Any]:
    pipe = store.get(pipeline_id)
    if pipe is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipe.to_public()


@app.get("/v1/pipelines/{pipeline_id}/script", response_class=PlainTextResponse)
async def download_script(pipeline_id: str) -> str:
    """Return generated Python script if code_generator ran successfully."""
    pipe = store.get(pipeline_id)
    if pipe is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    for r in reversed(pipe.results):
        if r.get("agent") == "code_generator" and r.get("status") == "ok" and r.get("script"):
            return str(r["script"])
    raise HTTPException(
        status_code=404,
        detail="No generated script. Run pipeline including code_generator first.",
    )


@app.post("/v1/pipelines/{pipeline_id}/run", response_model=PipelineOut)
async def run_pipeline(
    pipeline_id: str,
    file: UploadFile | None = File(None),
    path: str | None = Form(None),
    target_column: str | None = Form(None),
) -> dict[str, Any]:
    pipe = store.get(pipeline_id)
    if pipe is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    context: dict[str, Any] = {}
    if target_column:
        context["target_column"] = target_column

    if file is not None:
        content = await file.read()
        context["content"] = content
        context["filename"] = file.filename or "data.csv"
        context["source_filename"] = file.filename or "data.csv"
    elif path:
        context["path"] = path
        context["source_filename"] = path
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either a file upload or a path form field",
        )

    pipe.status = "running"
    store.update(pipe)

    result = await supervisor.run_pipeline(pipe.steps, context)

    pipe.status = result["status"]
    pipe.results = result.get("results", [])
    store.update(pipe)

    return pipe.to_public()
