from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True)

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_base_url: str = "http://127.0.0.1:8000"
    database_url: SecretStr | None = None
    database_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    openai_api_key: SecretStr | None = None
    langsmith_api_key: SecretStr | None = None
    langsmith_tracing: bool = False
    langsmith_project: str = "rag-researcher"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None or not value.get_secret_value().strip():
            return None
        try:
            url = make_url(value.get_secret_value())
            if url.drivername != "postgresql+asyncpg" or not url.host or not url.database:
                raise ValueError
        except Exception:
            raise ValueError("DATABASE_URL must be a PostgreSQL asyncpg URL with host and database") from None
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
