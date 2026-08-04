from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8080
    gateway_default_provider: str = "deepseek"

    deepseek_api_key: str | None = None
    openrouter_api_key: str | None = None
    nvidia_nim_api_key: str | None = None
    kimi_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"


@lru_cache
def get_settings() -> Settings:
    return Settings()
