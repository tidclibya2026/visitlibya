from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

SCRIPT = ROOT / "scripts" / "ingest_libya_boundary.py"


def test_ingestion_script_exists():
    assert SCRIPT.exists()


def test_ingestion_requires_governed_sha():
    content = SCRIPT.read_text(encoding="utf-8")

    assert (
        "0AF26F1911C5FE964E5B2B78D3A46401B93550AEF1ECC8AE342652A4C247B5E0"
        in content
    )


def test_ingestion_defaults_to_not_published():
    content = SCRIPT.read_text(encoding="utf-8")

    assert 'action="store_true"' in content
    assert "is_published=publish" in content


def test_ingestion_requires_single_boundary_feature():
    content = SCRIPT.read_text(encoding="utf-8")

    assert "Expected exactly one feature" in content
    assert "Expected Polygon or MultiPolygon" in content
    assert "geometry.is_valid" in content
