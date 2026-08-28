from __future__ import annotations

from sqlalchemy.orm import Session

from app.gis.layer_registry import (
    GovernedGISLayer,
    get_layer,
    public_layers,
    require_layer,
)
from app.repositories.governed_gis import GovernedGISRepository


class GovernedGISService:
    def __init__(self, session: Session) -> None:
        self.repository = GovernedGISRepository(session)

    def list_layers(self) -> tuple[GovernedGISLayer, ...]:
        return public_layers()

    def get_layer(self, layer_code: str) -> GovernedGISLayer | None:
        layer = get_layer(layer_code)
        if layer is None or not layer.frontend_visibility:
            return None
        return layer

    @staticmethod
    def validate_geometry_type(layer_code: str, geometry_type: str) -> GovernedGISLayer:
        layer = require_layer(layer_code)
        normalized_type = geometry_type.strip().upper()
        if normalized_type not in layer.allowed_geometry_types:
            raise ValueError(
                f"Geometry type {normalized_type} is not allowed for {layer.layer_code}"
            )
        return layer

    def get_public_features(
        self, layer_code: str, *, skip: int = 0, limit: int = 100
    ) -> list[dict]:
        layer = require_layer(layer_code)
        if not layer.frontend_visibility:
            return []
        features = self.repository.get_public_by_layer(
            layer.layer_code, skip=skip, limit=limit
        )
        return [
            {
                "id": feature.id,
                "layer_code": feature.layer_code,
                "feature_code": feature.feature_code,
                "name_ar": feature.name_ar,
                "name_en": feature.name_en,
                "category": feature.category,
                "geometry_type": feature.geometry_type,
            }
            for feature in features
        ]

    def get_public_feature(self, layer_code: str, feature_code: str) -> dict | None:
        layer = require_layer(layer_code)
        return self.repository.get_feature_geojson(layer.layer_code, feature_code)

    def get_public_geojson(self, layer_code: str, *, limit: int = 1000) -> dict:
        layer = require_layer(layer_code)
        return self.repository.get_public_geojson(layer.layer_code, limit=limit)

    def get_public_bbox_geojson(
        self,
        layer_code: str,
        *,
        min_longitude: float,
        min_latitude: float,
        max_longitude: float,
        max_latitude: float,
        limit: int = 1000,
    ) -> dict:
        layer = require_layer(layer_code)
        if min_longitude >= max_longitude or min_latitude >= max_latitude:
            raise ValueError("Bounding box minimums must be below maximums")
        if not (-180 <= min_longitude <= 180 and -180 <= max_longitude <= 180):
            raise ValueError("Bounding box longitude is outside WGS84 limits")
        if not (-90 <= min_latitude <= 90 and -90 <= max_latitude <= 90):
            raise ValueError("Bounding box latitude is outside WGS84 limits")
        return self.repository.get_public_bbox_geojson(
            layer.layer_code,
            min_longitude=min_longitude,
            min_latitude=min_latitude,
            max_longitude=max_longitude,
            max_latitude=max_latitude,
            limit=limit,
        )
