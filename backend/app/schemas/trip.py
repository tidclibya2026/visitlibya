from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.trip_constants import (
    MAX_TRIP_DESCRIPTION_LENGTH,
    MAX_TRIP_ITEM_NOTES_LENGTH,
    MAX_TRIP_ITEMS,
)
from app.models.trip import TripStatus, TripVisibility
from app.schemas.pagination import PaginatedResponse


class TripCreate(BaseModel):
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=MAX_TRIP_DESCRIPTION_LENGTH)
    start_date: date | None = None
    end_date: date | None = None
    status: TripStatus = TripStatus.DRAFT
    visibility: TripVisibility = TripVisibility.PRIVATE

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value


class TripUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=MAX_TRIP_DESCRIPTION_LENGTH)
    start_date: date | None = None
    end_date: date | None = None
    status: TripStatus | None = None
    visibility: TripVisibility | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("title must not be null")
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value

    @field_validator("status", "visibility")
    @classmethod
    def reject_null_required_fields(
        cls, value: TripStatus | TripVisibility | None
    ) -> TripStatus | TripVisibility:
        if value is None:
            raise ValueError("field must not be null")
        return value


class TripItemCreate(BaseModel):
    destination_id: int = Field(gt=0)
    day_number: int | None = Field(default=None, ge=1)
    visit_date: date | None = None
    start_time: time | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    sort_order: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=MAX_TRIP_ITEM_NOTES_LENGTH)


class TripItemUpdate(BaseModel):
    destination_id: int | None = Field(default=None, gt=0)
    day_number: int | None = Field(default=None, ge=1)
    visit_date: date | None = None
    start_time: time | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    sort_order: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=MAX_TRIP_ITEM_NOTES_LENGTH)

    @field_validator("destination_id", "day_number", "sort_order")
    @classmethod
    def reject_null_required_fields(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("field must not be null")
        return value


class TripItemReorderElement(BaseModel):
    item_id: int = Field(gt=0)
    day_number: int = Field(ge=1)


class TripItemReorderRequest(BaseModel):
    expected_version: int = Field(ge=1)
    items: list[TripItemReorderElement] = Field(
        min_length=1,
        max_length=MAX_TRIP_ITEMS,
    )


class TripDestinationSummary(BaseModel):
    id: int
    slug: str
    name_ar: str | None
    name_en: str | None


class TripItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination: TripDestinationSummary
    day_number: int
    visit_date: date | None
    start_time: time | None
    duration_minutes: int | None
    sort_order: int
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TripSummaryResponse(BaseModel):
    id: int
    title: str
    description: str | None
    start_date: date | None
    end_date: date | None
    status: TripStatus
    visibility: TripVisibility
    version: int
    duration_days: int | None
    item_count: int
    created_at: datetime
    updated_at: datetime


class TripDetailResponse(TripSummaryResponse):
    items: list[TripItemResponse]


class TripListResponse(PaginatedResponse[TripSummaryResponse]):
    pass
