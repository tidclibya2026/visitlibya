from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

from geoalchemy2.shape import from_shape
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.gis.layer_registry import GovernedGISLayer, require_layer
from app.models.governed_gis_feature import (
    GISAuthorityStatus,
    GISReviewStatus,
    GISValidationStatus,
    GovernedGISFeature,
)


class GovernedGISIngestionError(ValueError):
    """Raised when controlled GIS ingestion fails closed."""


@dataclass(frozen=True)
class ValidatedGISFeature:
    feature_code: str
    institutional_id: str
    source_feature_id: str
    geometry: BaseGeometry
    geometry_type: str
    properties: dict[str, Any]
    geometry_sha256: str


@dataclass(frozen=True)
class ValidatedGISInput:
    layer: GovernedGISLayer
    features: tuple[ValidatedGISFeature, ...]


def _canonical_geometry_sha256(geometry: BaseGeometry) -> str:
    payload = json.dumps(
        mapping(geometry), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest().upper()


def _validate_geometry(payload: object, layer: GovernedGISLayer) -> tuple[BaseGeometry, str]:
    if not isinstance(payload, dict):
        raise GovernedGISIngestionError("Feature geometry must be a GeoJSON object")
    declared_type = str(payload.get("type") or "").upper()
    if declared_type not in layer.allowed_geometry_types:
        raise GovernedGISIngestionError(
            f"Geometry type {declared_type or 'missing'} is not allowed for {layer.layer_code}"
        )
    try:
        geometry = shape(payload)
    except (TypeError, ValueError, KeyError) as exc:
        raise GovernedGISIngestionError("Feature geometry cannot be parsed") from exc
    geometry_type = geometry.geom_type.upper()
    if geometry_type not in layer.allowed_geometry_types:
        raise GovernedGISIngestionError(
            f"Parsed geometry type {geometry_type} is not allowed for {layer.layer_code}"
        )
    if geometry.is_empty:
        raise GovernedGISIngestionError("Feature geometry must not be empty")
    if not geometry.is_valid:
        raise GovernedGISIngestionError(
            f"Feature geometry is invalid: {explain_validity(geometry)}"
        )
    bounds = geometry.bounds
    if not all(math.isfinite(value) for value in bounds):
        raise GovernedGISIngestionError("Feature coordinates must be finite")
    min_x, min_y, max_x, max_y = bounds
    if min_x < -180 or max_x > 180 or min_y < -90 or max_y > 90:
        raise GovernedGISIngestionError(
            "Feature coordinates are outside global WGS84 longitude/latitude limits"
        )
    return geometry, geometry_type


def validate_geojson(path: Path, layer_code: str) -> ValidatedGISInput:
    layer = require_layer(layer_code)
    if layer.specialized_authority:
        raise GovernedGISIngestionError(
            f"{layer.layer_code} uses its specialized governed ingestion workflow"
        )
    if not path.is_file():
        raise FileNotFoundError(f"GeoJSON input not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GovernedGISIngestionError(f"Unable to read valid GeoJSON: {path}") from exc
    if not isinstance(payload, dict):
        raise GovernedGISIngestionError("GeoJSON root must be an object")
    if payload.get("type") == "Feature":
        raw_features = [payload]
    elif payload.get("type") == "FeatureCollection":
        raw_features = payload.get("features")
        if not isinstance(raw_features, list) or not raw_features:
            raise GovernedGISIngestionError(
                "FeatureCollection must contain at least one feature"
            )
    else:
        raise GovernedGISIngestionError("Input must be a GeoJSON Feature or FeatureCollection")

    validated: list[ValidatedGISFeature] = []
    identities: set[tuple[str, str]] = set()
    for index, feature in enumerate(raw_features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise GovernedGISIngestionError(f"Feature {index} is not a GeoJSON Feature")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise GovernedGISIngestionError(f"Feature {index} properties must be an object")
        feature_code = str(properties.get("feature_code") or "").strip()
        institutional_id = str(properties.get("institutional_id") or "").strip()
        source_feature_id = str(properties.get("source_feature_id") or "").strip()
        if not feature_code or not institutional_id or not source_feature_id:
            raise GovernedGISIngestionError(
                f"Feature {index} requires feature_code, institutional_id, and source_feature_id"
            )
        source_metadata = properties.get("source_metadata")
        if source_metadata is not None and not isinstance(source_metadata, dict):
            raise GovernedGISIngestionError(
                f"Feature {index} source_metadata must be an object"
            )
        identity = (feature_code, institutional_id)
        if identity in identities or any(
            item.feature_code == feature_code or item.institutional_id == institutional_id
            for item in validated
        ):
            raise GovernedGISIngestionError(
                f"Duplicate feature identity in input: {feature_code} / {institutional_id}"
            )
        identities.add(identity)
        geometry, geometry_type = _validate_geometry(feature.get("geometry"), layer)
        validated.append(
            ValidatedGISFeature(
                feature_code=feature_code,
                institutional_id=institutional_id,
                source_feature_id=source_feature_id,
                geometry=geometry,
                geometry_type=geometry_type,
                properties=properties,
                geometry_sha256=_canonical_geometry_sha256(geometry),
            )
        )
    return ValidatedGISInput(layer=layer, features=tuple(validated))


def _apply_feature(
    entity: GovernedGISFeature,
    feature: ValidatedGISFeature,
    validated: ValidatedGISInput,
    *,
    source_layer: str,
    source_database: str | None,
) -> None:
    properties = feature.properties
    entity.institutional_id = feature.institutional_id
    entity.layer_code = validated.layer.layer_code
    entity.feature_code = feature.feature_code
    entity.name_ar = properties.get("name_ar")
    entity.name_en = properties.get("name_en")
    entity.description_ar = properties.get("description_ar")
    entity.description_en = properties.get("description_en")
    entity.category = str(properties.get("category") or validated.layer.category)
    entity.geometry = from_shape(feature.geometry, srid=4326)
    entity.geometry_type = feature.geometry_type
    entity.source_owner = validated.layer.source_owner
    entity.institutional_reference = validated.layer.institutional_reference
    entity.source_database = source_database
    entity.source_layer = source_layer
    entity.source_feature_id = feature.source_feature_id
    entity.source_filter = properties.get("source_filter")
    entity.source_identity = properties.get("source_identity")
    entity.source_geometry_sha256 = feature.geometry_sha256
    entity.source_metadata = dict(properties.get("source_metadata") or {})
    entity.review_status = GISReviewStatus.UNDER_REVIEW
    entity.authority_status = GISAuthorityStatus.UNAPPROVED
    entity.validation_status = GISValidationStatus.VALID
    entity.is_validated = True
    entity.is_published = False
    entity.approved_at = None
    entity.published_at = None


def print_report(validated: ValidatedGISInput, *, dry_run: bool) -> None:
    print("GOVERNED GIS INGESTION DRY RUN" if dry_run else "GOVERNED GIS INGESTION COMPLETE")
    print("LAYER:", validated.layer.layer_code)
    print("FEATURE COUNT:", len(validated.features))
    print("GEOMETRY TYPES:", ",".join(sorted({f.geometry_type for f in validated.features})))
    print("REVIEW STATUS:", GISReviewStatus.UNDER_REVIEW.value)
    print("AUTHORITY STATUS:", GISAuthorityStatus.UNAPPROVED.value)
    print("VALIDATION STATUS:", GISValidationStatus.VALID.value)
    print("VALIDATED:", True)
    print("PUBLISHED:", False)


def ingest(
    *,
    geojson_path: Path,
    layer_code: str,
    source_layer: str,
    source_database: str | None = None,
    dry_run: bool = False,
    session_factory: Callable[[], Session] = SessionLocal,
) -> ValidatedGISInput:
    if not source_layer.strip():
        raise GovernedGISIngestionError("source_layer is required")
    validated = validate_geojson(geojson_path, layer_code)
    if dry_run:
        print_report(validated, dry_run=True)
        return validated
    session = session_factory()
    try:
        for feature in validated.features:
            matches = list(
                session.scalars(
                    select(GovernedGISFeature).where(
                        GovernedGISFeature.layer_code == validated.layer.layer_code,
                        or_(
                            GovernedGISFeature.feature_code == feature.feature_code,
                            GovernedGISFeature.institutional_id == feature.institutional_id,
                        ),
                    )
                ).all()
            )
            if len(matches) > 1:
                raise GovernedGISIngestionError(
                    f"Conflicting stored identities for {feature.feature_code}"
                )
            if matches:
                entity = matches[0]
                if (
                    entity.feature_code != feature.feature_code
                    or entity.institutional_id != feature.institutional_id
                ):
                    raise GovernedGISIngestionError(
                        f"Stored identity conflicts with {feature.feature_code}"
                    )
                if entity.is_published:
                    raise GovernedGISIngestionError(
                        f"Published feature {feature.feature_code} requires governed review"
                    )
            else:
                entity = GovernedGISFeature()
                session.add(entity)
            _apply_feature(
                entity, feature, validated,
                source_layer=source_layer.strip(),
                source_database=source_database,
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    print_report(validated, dry_run=False)
    return validated


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed institutional GIS ingestion")
    parser.add_argument("--geojson", required=True, type=Path)
    parser.add_argument("--layer-code", required=True)
    parser.add_argument("--source-layer", required=True)
    parser.add_argument("--source-database")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        ingest(
            geojson_path=args.geojson,
            layer_code=args.layer_code,
            source_layer=args.source_layer,
            source_database=args.source_database,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"GOVERNED GIS INGESTION FAILED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
