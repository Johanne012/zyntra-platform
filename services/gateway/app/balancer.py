"""Provider order strategies — ported ideas from free-claude-gateway, ZYNTRA-shaped."""

from __future__ import annotations

import itertools
import random
from typing import Literal

BalanceStrategy = Literal["priority", "round_robin", "random", "weighted"]


class ProviderBalancer:
    """Return an ordered try-list of provider ids."""

    def __init__(self, strategy: BalanceStrategy = "priority") -> None:
        self.strategy = strategy
        self._rr = itertools.count()

    def order(
        self,
        provider_ids: list[str],
        *,
        weights: dict[str, int] | None = None,
    ) -> list[str]:
        if not provider_ids:
            return []
        if self.strategy == "priority":
            return list(provider_ids)
        if self.strategy == "round_robin":
            start = next(self._rr) % len(provider_ids)
            return provider_ids[start:] + provider_ids[:start]
        if self.strategy == "random":
            out = list(provider_ids)
            random.shuffle(out)
            return out
        if self.strategy == "weighted":
            return self._weighted(provider_ids, weights or {})
        return list(provider_ids)

    def _weighted(self, ids: list[str], weights: dict[str, int]) -> list[str]:
        remaining = list(ids)
        result: list[str] = []
        while remaining:
            w_list = [max(1, weights.get(i, 1)) for i in remaining]
            total = sum(w_list)
            r = random.uniform(0, total)
            upto = 0.0
            chosen = 0
            for i, w in enumerate(w_list):
                upto += w
                if upto >= r:
                    chosen = i
                    break
            result.append(remaining.pop(chosen))
        return result
