from fastapi.testclient import TestClient
from app.main import app


def test_liveness_has_no_database_dependency(monkeypatch) -> None:
    monkeypatch.setattr("app.api.health.check_database_connection", lambda: (_ for _ in ()).throw(RuntimeError("must not run")))
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_controlled_failure(monkeypatch) -> None:
    monkeypatch.setattr("app.api.health.check_database_connection", lambda: False)
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert "database" not in response.text.lower()


def test_database_health_success_and_postgis_failure(monkeypatch) -> None:
    monkeypatch.setattr("app.api.health.check_database_connection", lambda: True)
    monkeypatch.setattr("app.api.health.check_postgis", lambda: True)
    with TestClient(app) as client:
        healthy = client.get("/health/db")
    monkeypatch.setattr("app.api.health.check_postgis", lambda: False)
    with TestClient(app) as client:
        failed = client.get("/health/db")
    assert healthy.status_code == 200 and healthy.json() == {"status": "ok"}
    assert failed.status_code == 503 and failed.json() == {"status": "unavailable"}


def test_readiness_requires_current_migration(monkeypatch) -> None:
    monkeypatch.setattr("app.api.health.check_database_connection", lambda: True)
    monkeypatch.setattr("app.api.health.check_postgis", lambda: True)
    monkeypatch.setattr("app.api.health.migration_is_current", lambda: False)
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503


def test_readiness_requires_postgis(monkeypatch) -> None:
    monkeypatch.setattr("app.api.health.check_database_connection", lambda: True)
    monkeypatch.setattr("app.api.health.check_postgis", lambda: False)
    monkeypatch.setattr("app.api.health.migration_is_current", lambda: True)
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
