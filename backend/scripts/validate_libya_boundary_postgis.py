from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.national_boundary import NationalBoundary
from scripts.ingest_libya_boundary import (
    COUNTRY_CODE, EXPECTED_SHP_SHA256, EXPECTED_SRID,
    INSTITUTIONAL_REFERENCE, NAME_AR, NAME_EN, SOURCE_DATABASE,
    SOURCE_FEATURE_CLASS, SOURCE_FEATURE_DATASET, SOURCE_FILTER,
    SOURCE_NAME_AR, SOURCE_NAME_EN, SOURCE_OWNER,
)


class BoundaryValidationError(ValueError):
    """Raised when the stored boundary fails governed validation."""


def validation_statement():
    geography = cast(NationalBoundary.geometry, Geography(srid=EXPECTED_SRID))
    extent = func.Box2D(NationalBoundary.geometry)
    return select(
        NationalBoundary.country_code,
        NationalBoundary.name_en,
        NationalBoundary.name_ar,
        NationalBoundary.source_name_en,
        NationalBoundary.source_name_ar,
        NationalBoundary.source_owner,
        NationalBoundary.institutional_reference,
        NationalBoundary.source_database,
        NationalBoundary.source_feature_dataset,
        NationalBoundary.source_feature_class,
        NationalBoundary.source_filter,
        NationalBoundary.source_geometry_sha256,
        NationalBoundary.is_validated,
        NationalBoundary.is_published,
        func.ST_IsValid(NationalBoundary.geometry).label("geometry_is_valid"),
        func.ST_SRID(NationalBoundary.geometry).label("geometry_srid"),
        func.GeometryType(NationalBoundary.geometry).label("geometry_type"),
        func.ST_NPoints(NationalBoundary.geometry).label("geometry_points"),
        func.ST_XMin(extent).label("min_x"),
        func.ST_YMin(extent).label("min_y"),
        func.ST_XMax(extent).label("max_x"),
        func.ST_YMax(extent).label("max_y"),
        (func.ST_Area(geography) / 1_000_000.0).label("area_km2"),
    ).where(NationalBoundary.country_code == COUNTRY_CODE)


EXPECTED_VALUES = {
    "country_code": COUNTRY_CODE,
    "name_en": NAME_EN,
    "name_ar": NAME_AR,
    "source_name_en": SOURCE_NAME_EN,
    "source_name_ar": SOURCE_NAME_AR,
    "source_owner": SOURCE_OWNER,
    "institutional_reference": INSTITUTIONAL_REFERENCE,
    "source_database": SOURCE_DATABASE,
    "source_feature_dataset": SOURCE_FEATURE_DATASET,
    "source_feature_class": SOURCE_FEATURE_CLASS,
    "source_filter": SOURCE_FILTER,
    "source_geometry_sha256": EXPECTED_SHP_SHA256,
    "is_validated": True,
    "is_published": False,
    "geometry_is_valid": True,
    "geometry_srid": EXPECTED_SRID,
    "geometry_type": "MULTIPOLYGON",
}


def validate_row(row: Mapping[str, Any]) -> None:
    failures = [
        f"{field}: expected {expected!r}, got {row.get(field)!r}"
        for field, expected in EXPECTED_VALUES.items()
        if row.get(field) != expected
    ]
    if failures:
        raise BoundaryValidationError("; ".join(failures))


def print_report(row: Mapping[str, Any]) -> None:
    print("LY NATIONAL BOUNDARY POSTGIS VALIDATION")
    print("RECORD COUNT: 1")
    for field in (
        "country_code", "name_en", "name_ar", "source_name_en", "source_name_ar",
        "source_owner", "institutional_reference", "source_database",
        "source_feature_dataset", "source_feature_class", "source_filter",
        "source_geometry_sha256", "is_validated", "is_published",
        "geometry_is_valid", "geometry_srid", "geometry_type", "geometry_points",
        "min_x", "min_y", "max_x", "max_y", "area_km2",
    ):
        print(f"{field.upper()}: {row[field]}")


def validate_database(
    session_factory: Callable[[], Session] = SessionLocal,
) -> Mapping[str, Any]:
    session = session_factory()
    try:
        rows = session.execute(validation_statement()).mappings().all()
        if len(rows) != 1:
            raise BoundaryValidationError(
                f"Expected exactly one LY boundary row, found {len(rows)}"
            )
        row = rows[0]
        validate_row(row)
        print_report(row)
        return row
    finally:
        session.close()


def main() -> int:
    try:
        validate_database()
    except Exception as exc:
        print(f"LY NATIONAL BOUNDARY VALIDATION FAILED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
