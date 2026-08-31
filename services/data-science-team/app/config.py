from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8082
    gateway_internal_url: str = "http://gateway:8080"
    log_level: str = "INFO"


settings = Settings()
