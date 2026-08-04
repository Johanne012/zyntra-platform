"""API key generation and hashing — never store raw keys."""

from __future__ import annotations

import hashlib
import secrets


def generate_api_key(prefix: str = "zyn") -> tuple[str, str, str]:
    """Return (raw_key, sha256_hex, key_prefix_for_display)."""
    raw = secrets.token_hex(32)
    full = f"{prefix}_{raw}"
    digest = hashlib.sha256(full.encode("utf-8")).hexdigest()
    display_prefix = full[:12]
    return full, digest, display_prefix


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
