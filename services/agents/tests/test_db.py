import asyncio

from app.config import Settings


def test_database_url_is_async() -> None:
    assert Settings(agents_database_url="sqlite+aiosqlite:///./data/test.db").agents_database_url.startswith("sqlite+aiosqlite://")


def test_event_loop_available_for_async_tests() -> None:
    async def probe() -> bool:
        return True

    assert asyncio.run(probe()) is True
