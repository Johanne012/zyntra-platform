"""Supervisor — routes tasks across specialized Data Science agents."""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.cleaner import CleanerAgent
from app.agents.data_loader import DataLoaderAgent
from app.agents.eda import EDAAgent
from app.agents.visualizer import VisualizerAgent


class Supervisor:
    """
    Lightweight supervisor that maintains a registry of agents
    and executes a sequential pipeline.
    """

    DEFAULT_PIPELINE = ["data_loader", "cleaner", "eda", "visualizer"]

    def __init__(self) -> None:
        self.agents: dict[str, BaseAgent] = {
            "data_loader": DataLoaderAgent(),
            "cleaner": CleanerAgent(),
            "eda": EDAAgent(),
            "visualizer": VisualizerAgent(),
        }

    def list_agents(self) -> list[dict[str, str]]:
        return [
            {"name": a.name, "description": a.description}
            for a in self.agents.values()
        ]

    async def run_step(
        self,
        agent_name: str,
        context: dict[str, Any],
        instruction: str = "",
    ) -> dict[str, Any]:
        agent = self.agents.get(agent_name)
        if agent is None:
            return {
                "status": "error",
                "error": f"Unknown agent: {agent_name}",
                "available": list(self.agents.keys()),
            }
        return await agent.run(context, instruction)

    async def run_pipeline(
        self,
        steps: list[str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a sequence of agents, passing enriched context between them."""
        results: list[dict[str, Any]] = []
        current = dict(context)

        for step in steps:
            result = await self.run_step(step, current)
            # Public result without internal objects
            public = {k: v for k, v in result.items() if not k.startswith("_")}
            results.append(public)

            if result.get("status") != "ok":
                return {
                    "status": "failed",
                    "failed_at": step,
                    "results": results,
                }

            if "_dataframe" in result:
                current["dataframe"] = result["_dataframe"]

        return {
            "status": "completed",
            "steps": steps,
            "results": results,
        }


supervisor = Supervisor()
