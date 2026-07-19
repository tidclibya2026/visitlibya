from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.review import ReviewStatus
from app.schemas.pagination import PaginatedResponse


class ReviewCreate(BaseModel):
    destination_id: int
    user_id: int | None = None
    reviewer_name: str | None = Field(default=None, max_length=200)
    reviewer_email: EmailStr | None = None
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=250)
    body: str = Field(min_length=1)


class ReviewUpdate(BaseModel):
    reviewer_name: str | None = Field(default=None, max_length=200)
    reviewer_email: EmailStr | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, max_length=250)
    body: str | None = Field(default=None, min_length=1)
    is_verified: bool | None = None

    @field_validator("rating", "body")
    @classmethod
    def reject_null_required_content(cls, value: object) -> object:
        if value is None:
            raise ValueError("rating and body cannot be null when provided")
        return value


class ReviewModerationUpdate(BaseModel):
    status: ReviewStatus


class ReviewRead(BaseModel):
    id: int
    destination_id: int
    user_id: int | None
    reviewer_name: str | None
    reviewer_email: EmailStr | None
    rating: int
    title: str | None
    body: str
    status: ReviewStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(PaginatedResponse[ReviewRead]):
    pass


ReviewSortField = Literal["id", "rating", "status", "created_at", "published_at"]
ReviewSortOrder = Literal["asc", "desc"]
