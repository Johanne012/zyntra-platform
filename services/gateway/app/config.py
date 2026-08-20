from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BalanceStrategy = Literal["priority", "round_robin", "random", "weighted"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8080
    gateway_default_provider: str = "deepseek"
    gateway_balance_strategy: BalanceStrategy = "priority"
    gateway_environment: Literal["development", "test", "production"] = "development"

    # In production the application refuses to start without a gateway key.
    gateway_api_key: str | None = None
    gateway_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    gateway_rate_limit_per_minute: int = 60
    gateway_stats_require_auth: bool = True

    deepseek_api_key: str | None = None
    openrouter_api_key: str | None = None
    nvidia_nim_api_key: str | None = None
    kimi_api_key: str | None = None
    groq_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"


@lru_cache
def get_settings() -> Settings:
    return Settings()
