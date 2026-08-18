#!/usr/bin/env python3
"""Small dependency-free health probe for the NEXUS core foundation."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


def main() -> int:
    payload = {
        "status": "ok",
        "service": "nexus-core",
        "version": "0.1.0",
        "time": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv("NODE_ENV", os.getenv("ENVIRONMENT", "unknown")),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
