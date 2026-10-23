"""Settings read from environment variables (see .env.example for every option)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://dcp:dcp@localhost:5432/dcp"
    log_level: str = "INFO"
    worker_poll_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
