import pytest
from fastapi.testclient import TestClient
from app.api.dependencies import get_category_service, get_current_active_user
from app.core.config import Settings
from app.main import app, create_app
from tests.integration.api.test_categories import FakeCategoryService


def test_admin_route_authorization(test_user, admin_user) -> None:
    body = {"code": "culture", "name_ar": "الثقافة", "name_en": "Culture"}
    app.dependency_overrides[get_category_service] = lambda: FakeCategoryService()
    try:
        with TestClient(app) as client:
            assert client.post("/api/v1/categories", json=body).status_code == 401
            app.dependency_overrides[get_current_active_user] = lambda: test_user
            assert client.post("/api/v1/categories", json=body).status_code == 403
            app.dependency_overrides[get_current_active_user] = lambda: admin_user
            assert client.post("/api/v1/categories", json=body).status_code == 201
    finally:
        app.dependency_overrides.clear()


PROTECTED_ROUTES = [
    ("post", "/api/v1/categories", {}),
    ("put", "/api/v1/categories/1", {}),
    ("delete", "/api/v1/categories/1", None),
    ("post", "/api/v1/destinations", {}),
    ("put", "/api/v1/destinations/1", {}),
    ("delete", "/api/v1/destinations/1", None),
    ("post", "/api/v1/media", {}),
    ("put", "/api/v1/media/1", {}),
    ("delete", "/api/v1/media/1", None),
    ("post", "/api/v1/media/1/destinations/1", {}),
    ("put", "/api/v1/media/1/destinations/1", {}),
    ("delete", "/api/v1/media/1/destinations/1", None),
    ("get", "/api/v1/reviews/admin", None),
    ("put", "/api/v1/reviews/admin/1", {}),
    ("patch", "/api/v1/reviews/admin/1/status", {}),
    ("delete", "/api/v1/reviews/admin/1", None),
]


@pytest.mark.parametrize("method,path,body", PROTECTED_ROUTES)
def test_every_admin_route_enforces_role(method, path, body, test_user, admin_user) -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        anonymous = client.request(method, path, json=body)
        app.dependency_overrides[get_current_active_user] = lambda: test_user
        ordinary = client.request(method, path, json=body)
        app.dependency_overrides[get_current_active_user] = lambda: admin_user
        authorized = client.request(method, path, json=body)
    app.dependency_overrides.clear()
    assert anonymous.status_code == 401
    assert ordinary.status_code == 403
    assert authorized.status_code not in {401, 403}


def _production_app():
    return create_app(Settings(
        _env_file=None, app_env="production", debug=False,
        database_url="postgresql+psycopg://u:p@db.example.test/db",
        jwt_secret_key="A9!bC2@dE3#fG4$hI5%jK6^lM7&nO8*pQ9(rS0)tU1+vW2=xY",
        cors_origins=["https://tidclibya2026.github.io"],
        trusted_hosts=["api.example.test", "testserver"], forwarded_allow_ips=["10.0.0.10"],
    ))


def test_production_cors_preflight_and_unknown_origin() -> None:
    with TestClient(_production_app()) as client:
        allowed = client.options("/api/v1/auth/me", headers={
            "Origin": "https://tidclibya2026.github.io",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type,X-Request-ID",
        })
        denied = client.get("/health/live", headers={"Origin": "https://unknown.example"})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://tidclibya2026.github.io"
    assert "authorization" in allowed.headers["access-control-allow-headers"].lower()
    assert "access-control-allow-origin" not in denied.headers


def test_security_headers_request_id_docs_and_trusted_hosts() -> None:
    with TestClient(_production_app()) as client:
        response = client.get("/health/live", headers={"X-Request-ID": "request-123"})
        docs = client.get("/docs")
        rejected = client.get("/health/live", headers={"Host": "evil.example"})
    assert response.status_code == 200 and response.headers["x-request-id"] == "request-123"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert docs.status_code == 404
    assert rejected.status_code == 400
