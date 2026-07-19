from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pagination import PaginatedResponse


class MediaAssetBase(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    original_file_name: str | None = Field(default=None, max_length=255)
    file_path: str = Field(min_length=1, max_length=1000)
    public_url: str | None = Field(default=None, max_length=1000)
    mime_type: str = Field(min_length=1, max_length=100)
    file_size: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    alt_ar: str | None = Field(default=None, max_length=500)
    alt_en: str | None = Field(default=None, max_length=500)
    caption_ar: str | None = None
    caption_en: str | None = None
    photographer: str | None = Field(default=None, max_length=250)
    source: str | None = Field(default=None, max_length=500)
    copyright_owner: str | None = Field(default=None, max_length=250)
    usage_rights: str | None = None
    is_active: bool = True


class MediaAssetCreate(MediaAssetBase):
    pass


class MediaAssetUpdate(BaseModel):
    file_name: str | None = Field(default=None, min_length=1, max_length=255)
    original_file_name: str | None = Field(default=None, max_length=255)
    file_path: str | None = Field(default=None, min_length=1, max_length=1000)
    public_url: str | None = Field(default=None, max_length=1000)
    mime_type: str | None = Field(default=None, min_length=1, max_length=100)
    file_size: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    alt_ar: str | None = Field(default=None, max_length=500)
    alt_en: str | None = Field(default=None, max_length=500)
    caption_ar: str | None = None
    caption_en: str | None = None
    photographer: str | None = Field(default=None, max_length=250)
    source: str | None = Field(default=None, max_length=500)
    copyright_owner: str | None = Field(default=None, max_length=250)
    usage_rights: str | None = None
    is_active: bool | None = None

    @field_validator("file_name", "file_path", "mime_type")
    @classmethod
    def validate_required_metadata(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("required media metadata cannot be null")
        return value


class DestinationMediaCreate(BaseModel):
    sort_order: int = Field(default=0, ge=0)
    is_primary: bool = False


class DestinationMediaUpdate(BaseModel):
    sort_order: int | None = Field(default=None, ge=0)
    is_primary: bool | None = None


class DestinationMediaRead(BaseModel):
    id: int
    destination_id: int
    media_id: int
    sort_order: int
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaAssetRead(MediaAssetBase):
    id: int
    destination_links: list[DestinationMediaRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaAssetListResponse(PaginatedResponse[MediaAssetRead]):
    pass


MediaSortField = Literal["id", "file_name", "mime_type", "file_size", "created_at"]
MediaSortOrder = Literal["asc", "desc"]
