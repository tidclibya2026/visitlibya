from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GeoJSONPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class DestinationGISProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    slug: str
    name_ar: str | None = None
    name_en: str | None = None
    category: str | None = None
    municipality: str | None = None
    region: str | None = None
    is_featured: bool = False


class DestinationGISFeature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONPoint
    properties: DestinationGISProperties


class DestinationGISFeatureCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[DestinationGISFeature] = Field(default_factory=list)
