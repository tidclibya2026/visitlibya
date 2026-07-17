from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Visit Libya API"
    app_version: str = "1.0.0"
    environment: str = "development"

    database_url: str = (
        "postgresql+psycopg://visitlibya:visitlibya_password"
        "@database:5432/visitlibya"
    )

    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()