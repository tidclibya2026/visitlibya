from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, NonNegativeInt, PositiveInt, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Visit Libya API"
    app_version: str = "2.0.1"
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"

    database_url: str
    db_pool_size: PositiveInt = 5
    db_max_overflow: NonNegativeInt = 10
    db_pool_timeout: PositiveInt = 30
    db_pool_recycle: PositiveInt = 1_800
    db_pool_pre_ping: bool = True

    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: PositiveInt = 30

    backend_cors_origins: list[str] = [
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
