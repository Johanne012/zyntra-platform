import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import app
from app.security import RateLimiter, parse_cors_origins, require_gateway_key
from fastapi import HTTPException


def test_parse_cors_star() -> None:
    assert parse_cors_origins("*") == ["*"]


def test_parse_cors_list() -> None:
    assert parse_cors_origins("http://a.com, http://b.com") == [
        "http://a.com",
        "http://b.com",
    ]


def test_require_key_open_when_unset() -> None:
    s = Settings(gateway_api_key=None)
    require_gateway_key(s, None, None)  # no raise


def test_require_key_rejects_missing() -> None:
    s = Settings(gateway_api_key="secret-key-value")
    with pytest.raises(HTTPException) as ei:
        require_gateway_key(s, None, None)
    assert ei.value.status_code == 401


def test_require_key_accepts_bearer() -> None:
    s = Settings(gateway_api_key="secret-key-value")
    require_gateway_key(s, "Bearer secret-key-value", None)


def test_rate_limiter_blocks() -> None:
    lim = RateLimiter(max_requests=2, window_sec=60)
    lim.check("ip1")
    lim.check("ip1")
    with pytest.raises(HTTPException) as ei:
        lim.check("ip1")
    assert ei.value.status_code == 429


@pytest.mark.asyncio
async def test_health_no_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["version"] == "0.3.0"
