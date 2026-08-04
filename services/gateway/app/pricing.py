"""Approximate USD cost per 1M tokens — for stats (not billing)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrice:
    input_per_million: float
    output_per_million: float


PRICING: dict[str, ModelPrice] = {
    "deepseek-chat": ModelPrice(0.14, 0.28),
    "deepseek-reasoner": ModelPrice(0.55, 2.19),
    "moonshot-v1-8k": ModelPrice(0.30, 0.30),
    "openai/gpt-4o-mini": ModelPrice(0.15, 0.60),
    "openai/gpt-4o": ModelPrice(2.50, 10.0),
    "meta/llama-3.1-8b-instruct": ModelPrice(0.0, 0.0),
    "llama-3.1-8b-instant": ModelPrice(0.05, 0.08),
    "llama-3.3-70b-versatile": ModelPrice(0.59, 0.79),
    "llama3.2": ModelPrice(0.0, 0.0),
}

DEFAULT_PRICE = ModelPrice(0.50, 1.50)


def get_price(model: str) -> ModelPrice:
    if not model:
        return DEFAULT_PRICE
    lower = model.lower().strip()
    if lower in PRICING:
        return PRICING[lower]
    short = lower.split("/")[-1]
    if short in PRICING:
        return PRICING[short]
    for key, price in PRICING.items():
        if key in lower or lower in key:
            return price
    return DEFAULT_PRICE


def calc_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = get_price(model)
    cost = (input_tokens / 1_000_000) * price.input_per_million
    cost += (output_tokens / 1_000_000) * price.output_per_million
    return round(cost, 8)
