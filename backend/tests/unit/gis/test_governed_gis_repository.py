from sqlalchemy.dialects import postgresql

from app.models.governed_gis_feature import GovernedGISFeature
from app.repositories.governed_gis import GovernedGISRepository


class FakeSession:
    pass


def compiled_public_query() -> str:
    from sqlalchemy import select
    filters = GovernedGISRepository._public_filters("NATURAL_SITES")
    return str(
        select(GovernedGISFeature.id)
        .where(*filters)
        .compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )


def test_public_methods_require_every_governance_gate():
    sql = compiled_public_query()
    assert "authority_status = 'approved'" in sql
    assert "validation_status = 'valid'" in sql
    assert "is_validated IS true" in sql
    assert "is_published IS true" in sql


def test_bbox_query_uses_postgis_intersection():
    repository = GovernedGISRepository(FakeSession())
    envelope = repository._envelope(10, 20, 15, 25)
    sql = str(envelope.compile(dialect=postgresql.dialect()))
    assert "ST_MakeEnvelope" in sql


def test_geojson_feature_projection_excludes_provenance():
    result = GovernedGISRepository._row_to_feature(
        {
            "id": 1, "layer_code": "NATURAL_SITES", "feature_code": "site-1",
            "name_ar": None, "name_en": "Site", "category": "natural_tourism",
            "geometry": '{"type":"Point","coordinates":[13,32]}',
        }
    )
    assert result["type"] == "Feature"
    assert result["geometry"]["type"] == "Point"
    assert "source_owner" not in result["properties"]
    assert "source_geometry_sha256" not in result["properties"]

