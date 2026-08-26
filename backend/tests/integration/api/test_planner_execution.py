from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user, get_planner_execution_service
from app.core.exceptions import DestinationNotFoundError, PlannerExecutionError, TripNotFoundError
from app.main import app
from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.schemas.planner_destination import PlannerDestinationAuthority


class FakeExecutionService:
    def __init__(self) -> None:
        self.calls = []
        self.error = None

    def execute(self, **values):
        self.calls.append(values)
        if self.error:
            raise self.error
        now = datetime.now(UTC)
        run = PlannerRun(
            id=5, user_id=values["actor_id"], trip_id=values["trip_id"],
            planner_version=1, engine_version="visitlibya-python-planner-v1",
            status=PlannerRunStatus.GENERATED, feasibility_score=95,
            input_snapshot={}, itinerary_snapshot={}, feasibility_snapshot={},
            recommendations_snapshot={}, optimization_snapshot={},
            created_at=now, updated_at=now,
        )
        authority = PlannerDestinationAuthority.model_validate({
            "destination_id": 1, "slug": "tripoli", "category_code": "historic-cities",
            "latitude": 32.8872, "longitude": 13.1913, "municipality": "Tripoli",
            "region": "Tripoli", "editorial_priority_order": 1,
            "publication_status": "published", "is_active": True,
            "translations": [], "profile_state": "unverified",
            "profile_verification_status": "unverified", "profile_verified_at": None,
            "operational_data": {
                "recommended_visit_minutes": 120, "minimum_visit_minutes": None,
                "maximum_visit_minutes": None, "opening_hours": None,
                "opening_hours_timezone": None, "access_status": None,
                "road_access": None, "road_surface": None, "road_condition": None,
                "planner_priority": 50, "meal_suitability": 50,
                "rest_suitability": 50, "data_source": None,
            },
        })
        return run, {"days": [], "feasibility": {"score": 95}}, [authority]

    def rollback(self):
        pass


PAYLOAD = {
    "destination_ids": [1], "days": 1, "pace": "balanced",
    "starting_point": "tripoli", "interests": ["history"],
    "traveler_type": "solo",
}


def install(service):
    app.dependency_overrides[get_current_active_user] = lambda: SimpleNamespace(id=7)
    app.dependency_overrides[get_planner_execution_service] = lambda: service


def test_execution_route_requires_authentication():
    with TestClient(app) as client:
        response = client.post("/api/v1/trips/22/planner-runs/execute", json=PAYLOAD)
    assert response.status_code == 401


def test_owned_execution_returns_generated_run_result_and_authority():
    service = FakeExecutionService(); install(service)
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/trips/22/planner-runs/execute", json=PAYLOAD)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["planner_run"]["status"] == "generated"
    assert response.json()["result"]["feasibility"]["score"] == 95
    assert response.json()["authority"][0]["profile_state"] == "unverified"
    assert service.calls[0]["actor_id"] == 7 and service.calls[0]["trip_id"] == 22


def test_execution_errors_are_deterministic_and_do_not_leak_details():
    cases = [
        (TripNotFoundError(), 404, "Trip not found"),
        (DestinationNotFoundError(), 404, "Destination not found"),
        (PlannerExecutionError(), 500, "Planner execution failed"),
    ]
    for error, status, detail in cases:
        service = FakeExecutionService(); service.error = error; install(service)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post("/api/v1/trips/22/planner-runs/execute", json=PAYLOAD)
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == status
        assert response.json() == {"detail": detail}


def test_invalid_or_empty_destination_input_returns_validation_error():
    service = FakeExecutionService(); install(service)
    try:
        with TestClient(app) as client:
            empty = client.post("/api/v1/trips/22/planner-runs/execute", json={**PAYLOAD, "destination_ids": []})
            invalid = client.post("/api/v1/trips/22/planner-runs/execute", json={**PAYLOAD, "pace": "impossible"})
    finally:
        app.dependency_overrides.clear()
    assert empty.status_code == 422 and invalid.status_code == 422
    assert service.calls == []
