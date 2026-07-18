from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Visit Libya API"
    app_version: str = "2.0.1"
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"

    database_url: str

    backend_cors_origins: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",")]

        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
