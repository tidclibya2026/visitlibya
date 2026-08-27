from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, shape
from shapely.validation import explain_validity
from sqlalchemy import select

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
SOURCE_DATABASE = "LibyaData.mdb"
SOURCE_FEATURE_DATASET = "الحدود"
SOURCE_FEATURE_CLASS = "الحدودالدولية"
SOURCE_FILTER = "Countries_EN = Libya"
SOURCE_NAME_EN = "Libya"
SOURCE_NAME_AR = "الجماهيرية العربية الليبية"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def load_geojson_geometry(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload.get("type") == "FeatureCollection":
        features = payload.get("features") or []

        if len(features) != 1:
            raise ValueError(
                f"Expected exactly one feature, found {len(features)}"
            )

        geometry_payload = features[0]["geometry"]

    elif payload.get("type") == "Feature":
        geometry_payload = payload["geometry"]

    else:
        geometry_payload = payload

    geometry = shape(geometry_payload)

    if geometry.geom_type == "Polygon":
        geometry = MultiPolygon([geometry])

    if geometry.geom_type != "MultiPolygon":
        raise ValueError(
            f"Expected Polygon or MultiPolygon, got {geometry.geom_type}"
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Geometry is invalid: {explain_validity(geometry)}"
        )

    return geometry


def ingest(
    *,
    geojson_path: Path,
    source_shp_path: Path,
    publish: bool,
) -> None:
    if not geojson_path.exists():
        raise FileNotFoundError(geojson_path)

    if not source_shp_path.exists():
        raise FileNotFoundError(source_shp_path)

    actual_sha = sha256_file(source_shp_path)

    if actual_sha != EXPECTED_SHP_SHA256:
        raise ValueError(
            "Source geometry SHA-256 does not match governed evidence. "
            f"Expected {EXPECTED_SHP_SHA256}, got {actual_sha}"
        )

    geometry = load_geojson_geometry(geojson_path)

    metadata = {
        "source_shp_sha256": actual_sha,
        "source_database": SOURCE_DATABASE,
        "feature_dataset": SOURCE_FEATURE_DATASET,
        "feature_class": SOURCE_FEATURE_CLASS,
        "source_filter": SOURCE_FILTER,
        "ingestion_source": str(geojson_path),
    }

    session = SessionLocal()

    try:
        boundary = session.scalar(
            select(NationalBoundary).where(
                NationalBoundary.country_code == COUNTRY_CODE
            )
        )

        if boundary is None:
            boundary = NationalBoundary(
                country_code=COUNTRY_CODE,
                name_en=NAME_EN,
                name_ar=NAME_AR,
                source_owner=SOURCE_OWNER,
                institutional_reference=INSTITUTIONAL_REFERENCE,
                source_database=SOURCE_DATABASE,
                source_feature_dataset=SOURCE_FEATURE_DATASET,
                source_feature_class=SOURCE_FEATURE_CLASS,
                source_filter=SOURCE_FILTER,
                source_name_en=SOURCE_NAME_EN,
                source_name_ar=SOURCE_NAME_AR,
                source_geometry_sha256=actual_sha,
                source_metadata=json.dumps(
                    metadata,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                geometry=from_shape(
                    geometry,
                    srid=4326,
                ),
                is_validated=True,
                is_published=publish,
            )

            session.add(boundary)

        else:
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
            boundary.source_geometry_sha256 = actual_sha
            boundary.source_metadata = json.dumps(
                metadata,
                ensure_ascii=False,
                sort_keys=True,
            )
            boundary.geometry = from_shape(
                geometry,
                srid=4326,
            )
            boundary.is_validated = True

            if publish:
                boundary.is_published = True

        session.commit()

        print("BOUNDARY INGESTION COMPLETE")
        print("COUNTRY:", COUNTRY_CODE)
        print("NAME:", NAME_EN, "/", NAME_AR)
        print("SHA256:", actual_sha)
        print("VALIDATED:", True)
        print("PUBLISHED:", publish)

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Governed Libya national boundary ingestion"
    )

    parser.add_argument(
        "--geojson",
        required=True,
        type=Path,
        help="Derived validated Libya boundary GeoJSON",
    )

    parser.add_argument(
        "--source-shp",
        required=True,
        type=Path,
        help="Governed source-derived shapefile used for SHA verification",
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help="Mark boundary public after ingestion",
    )

    args = parser.parse_args()

    ingest(
        geojson_path=args.geojson,
        source_shp_path=args.source_shp,
        publish=args.publish,
    )


if __name__ == "__main__":
    main()
