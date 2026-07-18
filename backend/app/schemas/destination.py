from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.destination import DestinationStatus


class DestinationTranslationBase(BaseModel):
    language_code: str = Field(
        min_length=2,
        max_length=10,
        examples=["ar"],
    )

    name: str = Field(
        min_length=2,
        max_length=250,
    )

    short_description: str | None = Field(
        default=None,
        max_length=500,
    )

    description: str | None = None
    historical_background: str | None = None
    visitor_information: str | None = None
    accessibility_information: str | None = None

    seo_title: str | None = Field(
        default=None,
        max_length=250,
    )

    seo_description: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("language_code")
    @classmethod
    def normalize_language_code(cls, value: str) -> str:
        return value.strip().lower()


class DestinationTranslationCreate(DestinationTranslationBase):
    pass


class DestinationTranslationRead(DestinationTranslationBase):
    id: int
    destination_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DestinationBase(BaseModel):
    slug: str = Field(
        min_length=2,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        examples=["leptis-magna"],
    )

    category_id: int | None = None
    status: DestinationStatus = DestinationStatus.DRAFT

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    municipality: str | None = Field(
        default=None,
        max_length=150,
    )

    region: str | None = Field(
        default=None,
        max_length=150,
    )

    priority_order: int = Field(
        default=0,
        ge=0,
    )

    is_featured: bool = False
    is_active: bool = True


class DestinationCreate(DestinationBase):
    translations: list[DestinationTranslationCreate] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_destination(self) -> "DestinationCreate":
        language_codes = [item.language_code.lower() for item in self.translations]
        if len(language_codes) != len(set(language_codes)):
            raise ValueError("Each translation language_code must be unique")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class DestinationUpdate(BaseModel):
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    category_id: int | None = None
    status: DestinationStatus | None = None

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    municipality: str | None = Field(
        default=None,
        max_length=150,
    )

    region: str | None = Field(
        default=None,
        max_length=150,
    )

    priority_order: int | None = Field(
        default=None,
        ge=0,
    )

    is_featured: bool | None = None
    is_active: bool | None = None

    translations: list[DestinationTranslationCreate] | None = Field(
        default=None,
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_translations(self) -> "DestinationUpdate":
        if self.translations is not None:
            language_codes = [item.language_code.lower() for item in self.translations]
            if len(language_codes) != len(set(language_codes)):
                raise ValueError("Each translation language_code must be unique")
        return self


class DestinationRead(DestinationBase):
    id: int
    translations: list[DestinationTranslationRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DestinationListResponse(BaseModel):
    items: list[DestinationRead]
    total: int
    skip: int
    limit: int
