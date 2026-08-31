"""In-memory pipeline store (Phase 1–2)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.supervisor import Supervisor


@dataclass
class Pipeline:
    id: str
    name: str
    status: str = "created"  # created | running | completed | failed
    steps: list[str] = field(default_factory=lambda: list(Supervisor.DEFAULT_PIPELINE))
    results: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "steps": self.steps,
            "results": self.results,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class PipelineStore:
    def __init__(self) -> None:
        self._pipelines: dict[str, Pipeline] = {}

    def create(self, name: str, steps: list[str] | None = None) -> Pipeline:
        pid = str(uuid.uuid4())
        pipe = Pipeline(
            id=pid,
            name=name,
            steps=steps or list(Supervisor.DEFAULT_PIPELINE),
        )
        self._pipelines[pid] = pipe
        return pipe

    def get(self, pipeline_id: str) -> Pipeline | None:
        return self._pipelines.get(pipeline_id)

    def list(self) -> list[Pipeline]:
        return list(self._pipelines.values())

    def update(self, pipeline: Pipeline) -> None:
        pipeline.updated_at = datetime.now(timezone.utc).isoformat()
        self._pipelines[pipeline.id] = pipeline


store = PipelineStore()
