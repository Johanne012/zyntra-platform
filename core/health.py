#!/usr/bin/env python3
"""Minimal dependency-free health probe for the NEXUS foundation."""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request


def http_check(url: str, timeout: float = 3.0) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return {"ok": 200 <= response.status < 400, "status": response.status}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def tcp_check(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def main() -> int:
    gateway = os.getenv("NEXUS_GATEWAY_URL", "http://127.0.0.1:8080/health")
    agents_host = os.getenv("NEXUS_AGENTS_HOST", "127.0.0.1")
    agents_port = int(os.getenv("NEXUS_AGENTS_PORT", "8081"))
    checks = {
        "gateway": http_check(gateway),
        "agents_tcp": {"ok": tcp_check(agents_host, agents_port)},
    }
    ok = all(item.get("ok") for item in checks.values())
    result = {"ok": ok, "checks": checks}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
