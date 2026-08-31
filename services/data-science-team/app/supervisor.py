"""Supervisor — routes tasks across specialized Data Science agents."""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.cleaner import CleanerAgent
from app.agents.code_generator import CodeGeneratorAgent
from app.agents.data_loader import DataLoaderAgent
from app.agents.eda import EDAAgent
from app.agents.feature_engineer import FeatureEngineerAgent
from app.agents.interpretability import InterpretabilityAgent
from app.agents.modeler import ModelerAgent
from app.agents.visualizer import VisualizerAgent


class Supervisor:
    DEFAULT_STEPS = [
        "data_loader",
        "cleaner",
        "eda",
        "visualizer",
        "feature_engineer",
        "modeler",
        "interpretability",
        "code_generator",
    ]

    def __init__(self) -> None:
        self.agents: dict[str, BaseAgent] = {
            "data_loader": DataLoaderAgent(),
            "cleaner": CleanerAgent(),
            "eda": EDAAgent(),
            "visualizer": VisualizerAgent(),
            "feature_engineer": FeatureEngineerAgent(),
            "modeler": ModelerAgent(),
            "interpretability": InterpretabilityAgent(),
            "code_generator": CodeGeneratorAgent(),
        }

    def list_agents(self) -> list[dict[str, str]]:
        return [{"name": a.name, "description": a.description} for a in self.agents.values()]

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
        results: list[dict[str, Any]] = []
        current = dict(context)

        for step in steps:
            # Feed accumulated public results to code_generator
            if step == "code_generator":
                current["pipeline_results"] = list(results)

            result = await self.run_step(step, current)
            results.append({k: v for k, v in result.items() if not k.startswith("_")})

            if result.get("status") != "ok":
                return {
                    "status": "failed",
                    "failed_at": step,
                    "results": results,
                }

            if "_dataframe" in result:
                current["dataframe"] = result["_dataframe"]
            if "_feature_columns" in result:
                current["feature_columns"] = result["_feature_columns"]
            if "_model" in result:
                current["model"] = result["_model"]
                current["_model"] = result["_model"]
            if "_target_column" in result:
                current["target_column"] = result["_target_column"]
            for key in ("_X_train", "_y_train", "_X_test", "_y_test"):
                if key in result:
                    current[key] = result[key]
                    current[key[1:]] = result[key]
            if result.get("agent") == "data_loader" and result.get("source"):
                current["source_filename"] = result["source"]

        return {
            "status": "completed",
            "steps": steps,
            "results": results,
        }


supervisor = Supervisor()
