"""Base agent interface for the Data Science Team."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """All specialized agents inherit from this."""

    name: str = "base"
    description: str = "Base agent"

    @abstractmethod
    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        """Execute the agent and return a result payload."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
