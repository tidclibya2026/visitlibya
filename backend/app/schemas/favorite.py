from datetime import datetime

from pydantic import BaseModel

from app.schemas.pagination import PaginatedResponse


class FavoriteCategoryItem(BaseModel):
    id: int
    code: str
    name_ar: str
    name_en: str


class FavoriteDestinationItem(BaseModel):
    id: int
    slug: str
    name_ar: str | None
    name_en: str | None
    municipality: str | None
    region: str | None
    category: FavoriteCategoryItem | None
    primary_media_url: str | None
    is_featured: bool


class FavoriteRead(BaseModel):
    id: int
    destination: FavoriteDestinationItem
    created_at: datetime


class FavoriteListResponse(PaginatedResponse[FavoriteRead]):
    pass


class FavoriteCheckResponse(BaseModel):
    destination_id: int
    is_favorite: bool
