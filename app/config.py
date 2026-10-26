"""Settings read from environment variables (see .env.example for every option)."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://dcp:dcp@localhost:5432/dcp"
    log_level: str = "INFO"
    worker_poll_seconds: float = 1.0
    # Master key that webhook signing secrets are derived from. Changing it changes every
    # endpoint's secret, so keep it stable and back it up with the database.
    dcp_secret_key: str = Field(min_length=32)
    webhook_timeout_seconds: float = 10.0
    # Quality checks: where local files live (file:// URIs must be inside it), an optional
    # S3-compatible endpoint (e.g. Cloudflare R2), and a cap on records read per batch.
    # S3 credentials come from the standard AWS settings (AWS_ACCESS_KEY_ID, ...).
    dcp_local_data_dir: str = "/data"
    dcp_s3_endpoint_url: str | None = None
    dcp_check_max_records: int = 5_000_000
    # The built web interface; served at / when present (it is, in the Docker image).
    dcp_web_dir: str = "/srv/web"

    @field_validator("dcp_secret_key")
    @classmethod
    def not_the_example(cls, value: str) -> str:
        if value.startswith("change-me"):
            raise ValueError(
                "DCP_SECRET_KEY is still the example value. Generate one with: "
                'python3 -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
