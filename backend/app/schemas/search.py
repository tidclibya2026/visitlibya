from math import ceil
from typing import Literal

from pydantic import BaseModel, Field, model_validator

class SearchFilters(BaseModel):
    q: str | None = Field(default=None, max_length=250)
    category_id: int | None = Field(default=None, ge=1)
    city: str | None = Field(default=None, max_length=150)
    region: str | None = Field(default=None, max_length=150)
    is_featured: bool | None = None
    minimum_rating: float | None = Field(default=None, ge=1, le=5)
    maximum_rating: float | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def validate_rating_range(self) -> "SearchFilters":
        if (
            self.minimum_rating is not None
            and self.maximum_rating is not None
            and self.minimum_rating > self.maximum_rating
        ):
            raise ValueError("minimum_rating cannot exceed maximum_rating")
        return self


class SearchCategoryItem(BaseModel):
    id: int
    code: str
    name_ar: str
    name_en: str


class SearchDestinationItem(BaseModel):
    id: int
    slug: str
    name_ar: str | None
    name_en: str | None
    short_description_ar: str | None
    short_description_en: str | None
    municipality: str | None
    region: str | None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    category: SearchCategoryItem | None
    primary_media_url: str | None
    is_featured: bool
    average_rating: float | None
    reviews_count: int

    @model_validator(mode="after")
    def validate_coordinate_pair(self) -> "SearchDestinationItem":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class SearchDestinationResponse(BaseModel):
    items: list[SearchDestinationItem]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        *,
        items: list[SearchDestinationItem],
        total: int,
        page: int,
        page_size: int,
    ) -> "SearchDestinationResponse":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=ceil(total / page_size) if total else 0,
        )


SearchSortField = Literal[
    "name",
    "created_at",
    "updated_at",
    "average_rating",
    "reviews_count",
]
SearchSortOrder = Literal["asc", "desc"]
