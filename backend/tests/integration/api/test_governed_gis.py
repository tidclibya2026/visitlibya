from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_layer_registry_endpoint_exposes_policy_not_source_paths():
    response = client.get("/api/v1/gis/layers")
    assert response.status_code == 200
    layers = response.json()
    assert any(layer["layer_code"] == "WORLD_HERITAGE" for layer in layers)
    assert all("source_database" not in layer for layer in layers)
    assert all("source_geometry_sha256" not in layer for layer in layers)


def test_unknown_layer_is_not_exposed():
    response = client.get("/api/v1/gis/layers/UNKNOWN_LAYER")
    assert response.status_code == 404


def test_unpublished_feature_is_not_exposed(monkeypatch):
    monkeypatch.setattr(
        "app.services.governed_gis.GovernedGISService.get_public_feature",
        lambda self, layer_code, feature_code: None,
    )
    response = client.get("/api/v1/gis/layers/NATURAL_SITES/features/draft-site")
    assert response.status_code == 404


def test_national_boundary_api_remains_publication_gated(monkeypatch):
    monkeypatch.setattr(
        "app.services.national_boundary.NationalBoundaryService.get_public_boundary",
        lambda self, country_code: None,
    )
    response = client.get("/api/v1/gis/boundaries/libya")
    assert response.status_code == 404
    assert response.json()["detail"] == "Published Libya national boundary is not available"

