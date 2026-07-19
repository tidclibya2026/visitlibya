import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pagination import PaginatedResponse


class CategoryBase(BaseModel):
    code: str = Field(min_length=2, max_length=100, examples=["archaeological-sites"])
    name_ar: str = Field(min_length=2, max_length=200)
    name_en: str = Field(min_length=2, max_length=200)
    description_ar: str | None = None
    description_en: str | None = None
    icon: str | None = Field(default=None, max_length=100)
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
            raise ValueError("code must contain lowercase letters, numbers, and hyphens")
        return normalized


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=100)
    name_ar: str | None = Field(default=None, min_length=2, max_length=200)
    name_en: str | None = Field(default=None, min_length=2, max_length=200)
    description_ar: str | None = None
    description_en: str | None = None
    icon: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("code cannot be null")
        normalized = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
            raise ValueError("code must contain lowercase letters, numbers, and hyphens")
        return normalized

    @field_validator("name_ar", "name_en")
    @classmethod
    def validate_required_names(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("category names cannot be null")
        return value


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(PaginatedResponse[CategoryRead]):
    pass
