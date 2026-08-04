"""In-memory usage + latency metrics (resets on restart)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class ProviderStats:
    requests: int = 0
    successes: int = 0
    failures: int = 0
    rate_limits: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    latency_samples: deque[float] = field(default_factory=lambda: deque(maxlen=200))
    last_used: float | None = None
    last_error: str | None = None
    last_latency_ms: float | None = None
    cooldown_until: float = 0.0


class StatsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self.started_at = time.time()
        self.total_requests = 0
        self.total_cost_usd = 0.0
        self.providers: dict[str, ProviderStats] = defaultdict(ProviderStats)

    def record_success(
        self,
        provider: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float | None = None,
    ) -> None:
        with self._lock:
            self.total_requests += 1
            self.total_cost_usd += cost_usd
            s = self.providers[provider]
            s.requests += 1
            s.successes += 1
            s.total_input_tokens += input_tokens
            s.total_output_tokens += output_tokens
            s.total_cost_usd += cost_usd
            s.last_used = time.time()
            s.last_error = None
            if latency_ms is not None:
                s.total_latency_ms += latency_ms
                s.latency_samples.append(latency_ms)
                s.last_latency_ms = latency_ms

    def record_failure(
        self,
        provider: str,
        error: str,
        *,
        is_rate_limit: bool = False,
        cooldown_sec: int = 60,
        latency_ms: float | None = None,
    ) -> None:
        with self._lock:
            self.total_requests += 1
            s = self.providers[provider]
            s.requests += 1
            s.failures += 1
            s.last_used = time.time()
            s.last_error = error[:200]
            if latency_ms is not None:
                s.latency_samples.append(latency_ms)
                s.last_latency_ms = latency_ms
            if is_rate_limit:
                s.rate_limits += 1
                s.cooldown_until = time.time() + cooldown_sec

    def is_in_cooldown(self, provider: str) -> bool:
        with self._lock:
            s = self.providers.get(provider)
            if not s:
                return False
            return time.time() < s.cooldown_until

    @staticmethod
    def _percentile(samples: list[float], p: float) -> float | None:
        if not samples:
            return None
        ordered = sorted(samples)
        idx = min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))
        return round(ordered[idx], 2)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            now = time.time()
            providers_data = {}
            for name, s in self.providers.items():
                samples = list(s.latency_samples)
                avg_lat = round(s.total_latency_ms / s.successes, 2) if s.successes else None
                success_rate = round(100.0 * s.successes / s.requests, 2) if s.requests else None
                providers_data[name] = {
                    "requests": s.requests,
                    "successes": s.successes,
                    "failures": s.failures,
                    "rate_limits": s.rate_limits,
                    "success_rate_pct": success_rate,
                    "input_tokens": s.total_input_tokens,
                    "output_tokens": s.total_output_tokens,
                    "cost_usd": round(s.total_cost_usd, 8),
                    "latency_ms": {
                        "last": s.last_latency_ms,
                        "avg": avg_lat,
                        "p50": self._percentile(samples, 50),
                        "p95": self._percentile(samples, 95),
                        "p99": self._percentile(samples, 99),
                        "samples": len(samples),
                    },
                    "last_used": s.last_used,
                    "last_error": s.last_error,
                    "in_cooldown": now < s.cooldown_until,
                    "cooldown_remaining_sec": max(0, int(s.cooldown_until - now)),
                }
            return {
                "uptime_seconds": int(now - self.started_at),
                "total_requests": self.total_requests,
                "total_cost_usd": round(self.total_cost_usd, 8),
                "providers": providers_data,
            }


stats = StatsCollector()
