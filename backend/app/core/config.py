from functools import lru_cache
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit
import ipaddress

from pydantic import AliasChoices, Field, NonNegativeInt, PositiveInt, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url

Environment = Literal["development", "test", "staging", "production"]
DatabaseSSLMode = Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
StringList = Annotated[list[str], NoDecode]


def _parse_list(value: Any) -> Any:
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("["):
            import json
            return json.loads(raw)
        return [item.strip() for item in raw.split(",") if item.strip()]
    return value


def _valid_origin(origin: str) -> bool:
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError:
        return False
    return bool(parsed.scheme in {"http", "https"} and parsed.hostname
                and not parsed.username and not parsed.password
                and parsed.path in {"", "/"} and not parsed.query and not parsed.fragment
                and origin == origin.rstrip("/"))


class Settings(BaseSettings):
    app_name: str = "Visit Libya API"
    app_version: str = "2.0.1"
    app_env: Environment = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    database_url_secret: SecretStr = Field(
        validation_alias=AliasChoices("DATABASE_URL", "database_url"), repr=False
    )
    database_pool_size: PositiveInt = 5
    database_max_overflow: NonNegativeInt = 10
    database_pool_timeout: PositiveInt = 30
    database_pool_recycle: PositiveInt = 1_800
    database_connect_timeout: PositiveInt = 10
    database_ssl_mode: DatabaseSSLMode | None = None
    database_pool_pre_ping: bool = True
    jwt_secret_key: SecretStr = Field(min_length=32, repr=False)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1_440)
    cors_origins: StringList = ["http://localhost:5500", "http://127.0.0.1:5500"]
    cors_allow_credentials: bool = True
    trusted_hosts: StringList = ["localhost", "127.0.0.1", "testserver"]
    forwarded_allow_ips: StringList = ["127.0.0.1"]
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"
    enable_docs: bool | None = None
    enable_redoc: bool | None = None
    enable_openapi: bool | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      case_sensitive=False, extra="ignore", populate_by_name=True)

    @field_validator("cors_origins", "trusted_hosts", "forwarded_allow_ips", mode="before")
    @classmethod
    def parse_lists(cls, value: Any) -> Any:
        return _parse_list(value)

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, origins: list[str]) -> list[str]:
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        if len(set(origins)) != len(origins):
            raise ValueError("CORS_ORIGINS must not contain duplicates")
        if "*" in origins:
            raise ValueError("wildcard CORS origins are not permitted")
        if any(not _valid_origin(origin) for origin in origins):
            raise ValueError("CORS origins must contain only scheme, host, and optional port")
        return origins

    @field_validator("trusted_hosts", "forwarded_allow_ips")
    @classmethod
    def validate_nonempty_lists(cls, values: list[str]) -> list[str]:
        if not values or any(not value.strip() for value in values):
            raise ValueError("host and proxy allowlists must not be empty")
        return values

    @field_validator("trusted_hosts")
    @classmethod
    def validate_trusted_host_syntax(cls, values: list[str]) -> list[str]:
        forbidden = ("://", "/", "?", "#", "@")
        if any(any(token in value for token in forbidden) or any(ch.isspace() for ch in value) for value in values):
            raise ValueError("TRUSTED_HOSTS must contain hostnames only")
        return values

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/") or value.endswith("/"):
            raise ValueError("API_PREFIX must start with one slash and have no trailing slash")
        return value

    @model_validator(mode="after")
    def validate_environment_policy(self) -> "Settings":
        docs_default = self.app_env in {"development", "test"}
        if self.enable_docs is None: self.enable_docs = docs_default
        if self.enable_redoc is None: self.enable_redoc = docs_default
        if self.enable_openapi is None: self.enable_openapi = docs_default
        if self.app_env == "production":
            missing = {"debug", "cors_origins", "trusted_hosts"} - self.model_fields_set
            if missing:
                raise ValueError("production requires explicit DEBUG, CORS_ORIGINS, and TRUSTED_HOSTS")
            if self.debug: raise ValueError("DEBUG must be false in production")
            if any("*" in host for host in self.trusted_hosts): raise ValueError("wildcard TRUSTED_HOSTS are not permitted in production")
            if "*" in self.forwarded_allow_ips: raise ValueError("wildcard FORWARDED_ALLOW_IPS are not permitted in production")
            try:
                for address in self.forwarded_allow_ips: ipaddress.ip_network(address, strict=False)
            except ValueError as exc:
                raise ValueError("production FORWARDED_ALLOW_IPS must contain IP addresses or networks") from exc
            if "https://tidclibya2026.github.io" not in self.cors_origins:
                raise ValueError("production CORS_ORIGINS must include the confirmed frontend origin")
            try: url = make_url(self.database_url)
            except Exception as exc: raise ValueError("DATABASE_URL is invalid") from exc
            if url.get_backend_name() != "postgresql": raise ValueError("production DATABASE_URL must use PostgreSQL")
            if (url.host or "").lower() in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("production DATABASE_URL must not use a loopback host")
            secret = self.jwt_secret_key.get_secret_value()
            weak = ("placeholder", "replace", "example", "change-me", "test-only")
            if len(secret) < 48 or len(set(secret)) < 12 or any(item in secret.lower() for item in weak):
                raise ValueError("JWT_SECRET_KEY does not meet production quality requirements")
        return self

    environment = property(lambda self: self.app_env)
    database_url = property(lambda self: self.database_url_secret.get_secret_value())
    api_v1_prefix = property(lambda self: self.api_prefix)
    backend_cors_origins = property(lambda self: self.cors_origins)
    db_pool_size = property(lambda self: self.database_pool_size)
    db_max_overflow = property(lambda self: self.database_max_overflow)
    db_pool_timeout = property(lambda self: self.database_pool_timeout)
    db_pool_recycle = property(lambda self: self.database_pool_recycle)
    db_pool_pre_ping = property(lambda self: self.database_pool_pre_ping)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
