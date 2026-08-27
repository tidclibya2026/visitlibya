from typing import Any, Literal

from pydantic import BaseModel


class NationalBoundaryProperties(BaseModel):
    country_code: str
    name_en: str
    name_ar: str


class NationalBoundaryFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: int
    properties: NationalBoundaryProperties
    geometry: dict[str, Any]
