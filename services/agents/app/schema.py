"""Small validation helpers for persisted JSON-like workflow definitions."""

from __future__ import annotations

import json
from typing import Any


def parse_definition(raw: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("workflow definition must be a JSON object")
    return value
