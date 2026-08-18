from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    agents_host: str = "0.0.0.0"
    agents_port: int = 8081
    agents_database_url: str = "sqlite+aiosqlite:///./data/agents.db"
    # Must be supplied in production; the previous hard-coded default was unsafe.
    agents_secret_key: str = ""
    gateway_internal_url: str = "http://127.0.0.1:8080"
    # Same as GATEWAY_API_KEY when gateway auth is enabled.
    gateway_api_key_internal: str | None = None
    agents_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
