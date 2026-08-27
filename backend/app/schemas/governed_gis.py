from typing import Any, Literal

from pydantic import BaseModel, Field


class GovernedGISLayerPublic(BaseModel):
    layer_code: str
    name_ar: str
    name_en: str
    category: str
    geometry_family: str
    allowed_geometry_types: list[str]
    authority_level: str
    publication_policy: str
    frontend_visibility: bool
    notes: str
    specialized_authority: bool


class GovernedGISFeatureSummary(BaseModel):
    id: int
    layer_code: str
    feature_code: str
    name_ar: str | None
    name_en: str | None
    category: str
    geometry_type: str


class GovernedGISFeatureProperties(BaseModel):
    layer_code: str
    feature_code: str
    name_ar: str | None
    name_en: str | None
    category: str


class GovernedGISGeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: int
    properties: GovernedGISFeatureProperties
    geometry: dict[str, Any]


class GovernedGISFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GovernedGISGeoJSONFeature]


class GovernedGISFeatureList(BaseModel):
    items: list[GovernedGISFeatureSummary]
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)

