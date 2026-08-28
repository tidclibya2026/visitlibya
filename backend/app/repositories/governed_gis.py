from __future__ import annotations

from collections.abc import Sequence
import json

from geoalchemy2 import Geometry
from sqlalchemy import Select, func, select
from sqlalchemy.sql.elements import ColumnElement

from app.models.governed_gis_feature import (
    GISAuthorityStatus,
    GISValidationStatus,
    GovernedGISFeature,
)
from app.repositories.base import BaseRepository


class GovernedGISRepository(BaseRepository[GovernedGISFeature]):
    @staticmethod
    def _public_filters(layer_code: str) -> tuple[ColumnElement[bool], ...]:
        return (
            GovernedGISFeature.layer_code == layer_code,
            GovernedGISFeature.authority_status == GISAuthorityStatus.APPROVED,
            GovernedGISFeature.validation_status == GISValidationStatus.VALID,
            GovernedGISFeature.is_validated.is_(True),
            GovernedGISFeature.is_published.is_(True),
            GovernedGISFeature.geometry.is_not(None),
        )

    def get_by_id(self, feature_id: int) -> GovernedGISFeature | None:
        return self.session.scalar(
            select(GovernedGISFeature).where(GovernedGISFeature.id == feature_id)
        )

    def get_by_feature_code(
        self, layer_code: str, feature_code: str
    ) -> GovernedGISFeature | None:
        return self.session.scalar(
            select(GovernedGISFeature).where(
                GovernedGISFeature.layer_code == layer_code,
                GovernedGISFeature.feature_code == feature_code,
            )
        )

    def get_by_institutional_id(
        self, layer_code: str, institutional_id: str
    ) -> GovernedGISFeature | None:
        return self.session.scalar(
            select(GovernedGISFeature).where(
                GovernedGISFeature.layer_code == layer_code,
                GovernedGISFeature.institutional_id == institutional_id,
            )
        )

    def get_by_layer_code(
        self, layer_code: str, *, skip: int = 0, limit: int = 100
    ) -> Sequence[GovernedGISFeature]:
        return self.session.scalars(
            select(GovernedGISFeature)
            .where(GovernedGISFeature.layer_code == layer_code)
            .order_by(GovernedGISFeature.id)
            .offset(skip)
            .limit(limit)
        ).all()

    def get_validated_by_layer(
        self, layer_code: str, *, skip: int = 0, limit: int = 100
    ) -> Sequence[GovernedGISFeature]:
        return self.session.scalars(
            select(GovernedGISFeature)
            .where(
                GovernedGISFeature.layer_code == layer_code,
                GovernedGISFeature.validation_status == GISValidationStatus.VALID,
                GovernedGISFeature.is_validated.is_(True),
            )
            .order_by(GovernedGISFeature.id)
            .offset(skip)
            .limit(limit)
        ).all()

    def get_public_by_layer(
        self, layer_code: str, *, skip: int = 0, limit: int = 1000
    ) -> Sequence[GovernedGISFeature]:
        return self.session.scalars(
            select(GovernedGISFeature)
            .where(*self._public_filters(layer_code))
            .order_by(GovernedGISFeature.id)
            .offset(skip)
            .limit(limit)
        ).all()

    def count_by_layer(self, layer_code: str) -> int:
        return self.session.scalar(
            select(func.count(GovernedGISFeature.id)).where(
                GovernedGISFeature.layer_code == layer_code
            )
        ) or 0

    @staticmethod
    def _envelope(
        min_longitude: float,
        min_latitude: float,
        max_longitude: float,
        max_latitude: float,
    ):
        return func.ST_MakeEnvelope(
            min_longitude, min_latitude, max_longitude, max_latitude, 4326,
            type_=Geometry(geometry_type="POLYGON", srid=4326),
        )

    def get_public_in_bbox(
        self,
        layer_code: str,
        *,
        min_longitude: float,
        min_latitude: float,
        max_longitude: float,
        max_latitude: float,
        skip: int = 0,
        limit: int = 1000,
    ) -> Sequence[GovernedGISFeature]:
        envelope = self._envelope(
            min_longitude, min_latitude, max_longitude, max_latitude
        )
        return self.session.scalars(
            select(GovernedGISFeature)
            .where(
                *self._public_filters(layer_code),
                func.ST_Intersects(GovernedGISFeature.geometry, envelope),
            )
            .order_by(GovernedGISFeature.id)
            .offset(skip)
            .limit(limit)
        ).all()

    @staticmethod
    def _geojson_statement(
        *filters: ColumnElement[bool], limit: int = 1000
    ) -> Select:
        return (
            select(
                GovernedGISFeature.id,
                GovernedGISFeature.layer_code,
                GovernedGISFeature.feature_code,
                GovernedGISFeature.name_ar,
                GovernedGISFeature.name_en,
                GovernedGISFeature.category,
                func.ST_AsGeoJSON(GovernedGISFeature.geometry, 6).label("geometry"),
            )
            .where(*filters)
            .order_by(GovernedGISFeature.id)
            .limit(limit)
        )

    @staticmethod
    def _row_to_feature(row: dict) -> dict:
        return {
            "type": "Feature",
            "id": row["id"],
            "properties": {
                "layer_code": row["layer_code"],
                "feature_code": row["feature_code"],
                "name_ar": row["name_ar"],
                "name_en": row["name_en"],
                "category": row["category"],
            },
            "geometry": json.loads(row["geometry"]),
        }

    def get_feature_geojson(self, layer_code: str, feature_code: str) -> dict | None:
        statement = self._geojson_statement(
            *self._public_filters(layer_code),
            GovernedGISFeature.feature_code == feature_code,
            limit=1,
        )
        row = self.session.execute(statement).mappings().first()
        return None if row is None else self._row_to_feature(row)

    def get_public_geojson(self, layer_code: str, *, limit: int = 1000) -> dict:
        rows = self.session.execute(
            self._geojson_statement(*self._public_filters(layer_code), limit=limit)
        ).mappings().all()
        return {
            "type": "FeatureCollection",
            "features": [self._row_to_feature(row) for row in rows],
        }

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
        envelope = self._envelope(
            min_longitude, min_latitude, max_longitude, max_latitude
        )
        rows = self.session.execute(
            self._geojson_statement(
                *self._public_filters(layer_code),
                func.ST_Intersects(GovernedGISFeature.geometry, envelope),
                limit=limit,
            )
        ).mappings().all()
        return {
            "type": "FeatureCollection",
            "features": [self._row_to_feature(row) for row in rows],
        }

