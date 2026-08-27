from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Callable

from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.national_boundary import NationalBoundary


EXPECTED_SHP_SHA256 = (
    "0AF26F1911C5FE964E5B2B78D3A46401B93550AEF1ECC8AE342652A4C247B5E0"
)
COUNTRY_CODE = "LY"
NAME_EN = "Libya"
NAME_AR = "ليبيا"
SOURCE_OWNER = "مركز المعلومات والتوثيق السياحي"
INSTITUTIONAL_REFERENCE = "المخطط العام للتنمية السياحية"
SOURCE_DATABASE = "atlas/LibyaData.mdb"
SOURCE_FEATURE_DATASET = "الحدود"
SOURCE_FEATURE_CLASS = "الحدودالدولية"
SOURCE_FILTER = "Countries_EN = Libya"
SOURCE_NAME_EN = "Libya"
SOURCE_NAME_AR = "الجماهيرية العربية الليبية"
EXPECTED_SRID = 4326


class BoundaryGovernanceError(ValueError):
    """Raised when governed ingestion requirements are not satisfied."""


@dataclass(frozen=True)
class GeometryValidation:
    geometry: BaseGeometry
    feature_count: int
    original_geometry_type: str

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return self.geometry.bounds


@dataclass(frozen=True)
class IngestionValidation:
    source_sha256: str
    geometry: GeometryValidation


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_source_shapefile(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Governed source shapefile not found: {path}")
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_SHP_SHA256:
        raise BoundaryGovernanceError(
            "Source geometry SHA-256 does not match governed evidence. "
            f"Expected {EXPECTED_SHP_SHA256}, got {actual_sha}"
        )
    return actual_sha


def _extract_geometry(payload: object) -> tuple[dict, int]:
    if not isinstance(payload, dict):
        raise BoundaryGovernanceError("GeoJSON root must be an object")
    payload_type = payload.get("type")
    if payload_type == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list):
            raise BoundaryGovernanceError("FeatureCollection features must be a list")
        if len(features) != 1:
            raise BoundaryGovernanceError(
                f"Expected exactly one feature, found {len(features)}"
            )
        feature = features[0]
        if not isinstance(feature, dict):
            raise BoundaryGovernanceError("GeoJSON feature must be an object")
        geometry_payload = feature.get("geometry")
        feature_count = len(features)
    elif payload_type == "Feature":
        geometry_payload = payload.get("geometry")
        feature_count = 1
    else:
        geometry_payload = payload
        feature_count = 1
    if geometry_payload is None:
        raise BoundaryGovernanceError("GeoJSON geometry is missing or null")
    if not isinstance(geometry_payload, dict):
        raise BoundaryGovernanceError("GeoJSON geometry must be an object")
    return geometry_payload, feature_count


def load_geojson_geometry(path: Path) -> GeometryValidation:
    if not path.is_file():
        raise FileNotFoundError(f"Derived GeoJSON not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BoundaryGovernanceError(f"Unable to read valid GeoJSON: {path}") from exc
    geometry_payload, feature_count = _extract_geometry(payload)
    declared_type = geometry_payload.get("type")
    if declared_type not in {"Polygon", "MultiPolygon"}:
        raise BoundaryGovernanceError(
            f"Expected Polygon or MultiPolygon, got {declared_type or 'missing type'}"
        )
    try:
        geometry = shape(geometry_payload)
    except (TypeError, ValueError, KeyError) as exc:
        raise BoundaryGovernanceError("GeoJSON geometry cannot be parsed") from exc
    original_geometry_type = geometry.geom_type
    if original_geometry_type == "Polygon":
        geometry = MultiPolygon([geometry])
    elif original_geometry_type != "MultiPolygon":
        raise BoundaryGovernanceError(
            f"Expected Polygon or MultiPolygon, got {original_geometry_type}"
        )
    if geometry.is_empty:
        raise BoundaryGovernanceError("Geometry must not be empty")
    if not geometry.is_valid:
        raise BoundaryGovernanceError(
            f"Geometry is invalid: {explain_validity(geometry)}"
        )
    min_x, min_y, max_x, max_y = geometry.bounds
    if not all(math.isfinite(value) for value in geometry.bounds):
        raise BoundaryGovernanceError("Geometry coordinates must be finite")
    if min_x < -180 or max_x > 180 or min_y < -90 or max_y > 90:
        raise BoundaryGovernanceError(
            "Geometry coordinates are not plausible WGS84 longitude/latitude values"
        )
    return GeometryValidation(geometry, feature_count, original_geometry_type)


def validate_inputs(
    *, geojson_path: Path, source_shp_path: Path
) -> IngestionValidation:
    source_sha256 = validate_source_shapefile(source_shp_path)
    geometry = load_geojson_geometry(geojson_path)
    return IngestionValidation(source_sha256, geometry)


def _metadata(validation: IngestionValidation, geojson_path: Path) -> str:
    return json.dumps(
        {
            "source_shp_sha256": validation.source_sha256,
            "source_database": SOURCE_DATABASE,
            "feature_dataset": SOURCE_FEATURE_DATASET,
            "feature_class": SOURCE_FEATURE_CLASS,
            "source_filter": SOURCE_FILTER,
            "ingestion_source": str(geojson_path),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _apply_governed_values(
    boundary: NationalBoundary,
    *,
    validation: IngestionValidation,
    geojson_path: Path,
    publish: bool,
) -> None:
    boundary.country_code = COUNTRY_CODE
    boundary.name_en = NAME_EN
    boundary.name_ar = NAME_AR
    boundary.source_owner = SOURCE_OWNER
    boundary.institutional_reference = INSTITUTIONAL_REFERENCE
    boundary.source_database = SOURCE_DATABASE
    boundary.source_feature_dataset = SOURCE_FEATURE_DATASET
    boundary.source_feature_class = SOURCE_FEATURE_CLASS
    boundary.source_filter = SOURCE_FILTER
    boundary.source_name_en = SOURCE_NAME_EN
    boundary.source_name_ar = SOURCE_NAME_AR
    boundary.source_geometry_sha256 = validation.source_sha256
    boundary.source_metadata = _metadata(validation, geojson_path)
    boundary.geometry = from_shape(validation.geometry.geometry, srid=EXPECTED_SRID)
    boundary.is_validated = True
    boundary.is_published = publish


def print_validation_report(
    validation: IngestionValidation, *, dry_run: bool, published: bool = False
) -> None:
    min_x, min_y, max_x, max_y = validation.geometry.bounds
    if dry_run:
        print("BOUNDARY INGESTION DRY RUN")
    print("FEATURE COUNT:", validation.geometry.feature_count)
    print("ORIGINAL GEOMETRY TYPE:", validation.geometry.original_geometry_type)
    print("NORMALIZED GEOMETRY TYPE:", validation.geometry.geometry.geom_type)
    print("VALID:", validation.geometry.geometry.is_valid)
    print("SRID EXPECTATION:", EXPECTED_SRID)
    print("MIN_X:", min_x)
    print("MIN_Y:", min_y)
    print("MAX_X:", max_x)
    print("MAX_Y:", max_y)
    print("SOURCE SHA256:", validation.source_sha256)
    print("COUNTRY:", COUNTRY_CODE)
    print("NAME_EN:", NAME_EN)
    print("NAME_AR:", NAME_AR)
    print("VALIDATED:", True)
    print("PUBLISHED:", published)


def ingest(
    *,
    geojson_path: Path,
    source_shp_path: Path,
    publish: bool = False,
    dry_run: bool = False,
    session_factory: Callable[[], Session] = SessionLocal,
) -> IngestionValidation:
    validation = validate_inputs(
        geojson_path=geojson_path, source_shp_path=source_shp_path
    )
    if dry_run:
        if publish:
            raise BoundaryGovernanceError("Dry-run cannot be combined with --publish")
        print_validation_report(validation, dry_run=True, published=False)
        return validation
    session = session_factory()
    try:
        boundaries = list(
            session.scalars(
                select(NationalBoundary).where(
                    NationalBoundary.country_code == COUNTRY_CODE
                )
            ).all()
        )
        if len(boundaries) > 1:
            raise BoundaryGovernanceError(
                "More than one LY boundary exists; institutional review is required"
            )
        if boundaries:
            boundary = boundaries[0]
            if boundary.is_published:
                raise BoundaryGovernanceError(
                    "The existing LY boundary is published; institutional review is "
                    "required before it can be replaced or unpublished"
                )
        else:
            boundary = NationalBoundary()
            session.add(boundary)
        _apply_governed_values(
            boundary,
            validation=validation,
            geojson_path=geojson_path,
            publish=publish,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    print("BOUNDARY INGESTION COMPLETE")
    print_validation_report(validation, dry_run=False, published=publish)
    return validation


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Governed Libya national boundary ingestion"
    )
    parser.add_argument("--geojson", required=True, type=Path)
    parser.add_argument("--source-shp", required=True, type=Path)
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Future explicit governance path: publish after institutional approval",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate without a database connection"
    )
    args = parser.parse_args()
    try:
        ingest(
            geojson_path=args.geojson,
            source_shp_path=args.source_shp,
            publish=args.publish,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"BOUNDARY INGESTION FAILED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
