import pytest

from app.config import Settings


def test_secret_has_no_insecure_default() -> None:
    assert Settings().agents_secret_key == ""


def test_cors_defaults_are_local_only() -> None:
    assert Settings().agents_cors_origins == "http://localhost:3000,http://127.0.0.1:3000"
