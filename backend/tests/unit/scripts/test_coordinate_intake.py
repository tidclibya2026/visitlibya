import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.coordinate_intake import (
    ReviewedCoordinateDataset,
    build_coordinate_merge,
    load_reviewed_coordinates,
    write_dataset_atomic,
)
from scripts.destination_import import ImportDataset, load_dataset
from scripts.merge_destination_coordinates import main


def canonical_payload(latitude=None, longitude=None) -> dict:
    return {
        "schema_version": 1,
        "dataset": "coordinate-test",
        "categories": [
            {"code": "heritage", "name_ar": "التراث", "name_en": "Heritage"}
        ],
        "records": [
            {
                "slug": "leptis-magna",
                "category": "heritage",
                "status": "published",
                "is_active": True,
                "latitude": latitude,
                "longitude": longitude,
                "translations": [
                    {"language_code": "ar", "name": "لبدة الكبرى"},
                    {"language_code": "en", "name": "Leptis Magna"},
                ],
            }
        ],
    }


def reviewed_payload(slug="leptis-magna", latitude=32.6, longitude=14.3) -> dict:
    return {
        "schema_version": 1,
        "source": "center-owned-destinations.kml / Placemark LM-001",
        "reviewed_by": None,
        "review_date": None,
        "records": [
            {
                "slug": slug,
                "latitude": latitude,
                "longitude": longitude,
                "source_reference": "Placemark LM-001",
                "status": "reviewed",
            }
        ],
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_valid_reviewed_file(tmp_path: Path) -> None:
    path = tmp_path / "reviewed.json"; write_json(path, reviewed_payload())
    dataset, digest = load_reviewed_coordinates(path)
    assert dataset.records[0].slug == "leptis-magna" and len(digest) == 64


def test_invalid_schema() -> None:
    payload = reviewed_payload(); payload["schema_version"] = 2
    with pytest.raises(ValidationError): ReviewedCoordinateDataset.model_validate(payload)


def test_duplicate_slug() -> None:
    payload = reviewed_payload(); payload["records"].append(dict(payload["records"][0]))
    with pytest.raises(ValidationError, match="slugs must be unique"):
        ReviewedCoordinateDataset.model_validate(payload)


def test_partial_coordinate_is_rejected() -> None:
    payload = reviewed_payload(); del payload["records"][0]["longitude"]
    with pytest.raises(ValidationError): ReviewedCoordinateDataset.model_validate(payload)


@pytest.mark.parametrize("field,value", [("latitude", 91), ("longitude", 181)])
def test_range_violation(field: str, value: float) -> None:
    payload = reviewed_payload(); payload["records"][0][field] = value
    with pytest.raises(ValidationError): ReviewedCoordinateDataset.model_validate(payload)


def test_unknown_slug_is_blocked() -> None:
    plan = build_coordinate_merge(
        ImportDataset.model_validate(canonical_payload()),
        ReviewedCoordinateDataset.model_validate(reviewed_payload(slug="unknown-site")),
    )
    assert "unknown-site" in plan.blocked and not plan.ready


def test_existing_coordinate_conflict() -> None:
    plan = build_coordinate_merge(
        ImportDataset.model_validate(canonical_payload(31.0, 13.0)),
        ReviewedCoordinateDataset.model_validate(reviewed_payload()),
    )
    assert "leptis-magna" in plan.conflicts and not plan.can_write


def test_exact_slug_merge() -> None:
    plan = build_coordinate_merge(
        ImportDataset.model_validate(canonical_payload()),
        ReviewedCoordinateDataset.model_validate(reviewed_payload()),
    )
    merged = plan.merged_dataset.records[0]
    assert plan.ready == ["leptis-magna"]
    assert (merged.latitude, merged.longitude) == (32.6, 14.3)


def test_preview_does_not_write(tmp_path: Path) -> None:
    canonical = tmp_path / "destinations.json"; reviewed = tmp_path / "reviewed.json"
    write_json(canonical, canonical_payload()); write_json(reviewed, reviewed_payload())
    before = canonical.read_bytes()
    assert main(["--dataset", str(canonical), "--coordinates", str(reviewed)]) == 0
    assert canonical.read_bytes() == before


def test_explicit_write_updates_dataset_only(tmp_path: Path) -> None:
    canonical = tmp_path / "destinations.json"; reviewed = tmp_path / "reviewed.json"
    write_json(canonical, canonical_payload()); write_json(reviewed, reviewed_payload())
    assert main([
        "--dataset", str(canonical), "--coordinates", str(reviewed), "--write-dataset"
    ]) == 0
    merged, _ = load_dataset(canonical)
    assert merged.records[0].latitude == 32.6


def test_atomic_writer_reports_hashes(tmp_path: Path) -> None:
    canonical = tmp_path / "destinations.json"; write_json(canonical, canonical_payload())
    dataset = ImportDataset.model_validate(canonical_payload(32.6, 14.3))
    before, after = write_dataset_atomic(canonical, dataset)
    assert before != after and len(before) == len(after) == 64


def test_reviewed_records_require_source() -> None:
    payload = reviewed_payload(); payload["source"] = None
    with pytest.raises(ValidationError, match="source is required"):
        ReviewedCoordinateDataset.model_validate(payload)


def test_public_source_url_is_rejected() -> None:
    payload = reviewed_payload(); payload["source"] = "https://example.com/coordinates"
    with pytest.raises(ValidationError, match="not a URL"):
        ReviewedCoordinateDataset.model_validate(payload)
