from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegistrationRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr = Field(max_length=320)
    username: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    )
    password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Full name is required")
        return normalized

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        checks = (
            any(character.islower() for character in value),
            any(character.isupper() for character in value),
            any(character.isdigit() for character in value),
            any(
                not character.isalnum() and not character.isspace()
                for character in value
            ),
        )
        if not all(checks):
            raise ValueError(
                "Password must include uppercase, lowercase, number, and symbol"
            )
        return value


class UserRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    full_name: str
    is_active: bool
    is_superuser: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    subject: int


class CurrentUserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    is_superuser: bool
    roles: list[str]
