from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import get_current_active_user, get_planner_run_service
from app.core.exceptions import TripNotFoundError
from app.main import app
from app.models.planner_run import PlannerRun, PlannerRunStatus


def make_run(**overrides) -> PlannerRun:
    now = datetime.now(UTC)
    values = {
        "id": 1, "user_id": 7, "trip_id": 22, "planner_version": 1,
        "engine_version": "visitlibya-ai-planner-v1",
        "status": PlannerRunStatus.GENERATED, "feasibility_score": 80,
        "input_snapshot": {}, "itinerary_snapshot": {},
        "feasibility_snapshot": {}, "recommendations_snapshot": {},
        "optimization_snapshot": {}, "created_at": now, "updated_at": now,
    }
    values.update(overrides)
    return PlannerRun(**values)


class FakePlannerRunService:
    def __init__(self) -> None:
        self.run = make_run()
        self.user_ids: list[int] = []
        self.rolled_back = False

    def create_run(self, *, user_id: int, trip_id: int | None, **_: object) -> PlannerRun:
        self.user_ids.append(user_id)
        if trip_id == 404:
            raise TripNotFoundError()
        return make_run(user_id=user_id, trip_id=trip_id)

    def get_owned_run(self, *, planner_run_id: int, user_id: int) -> PlannerRun | None:
        self.user_ids.append(user_id)
        return None if planner_run_id == 404 else self.run

    def list_user_runs(self, *, user_id: int, **_: int) -> list[PlannerRun]:
        self.user_ids.append(user_id)
        return [self.run]

    def list_trip_runs(self, *, trip_id: int, user_id: int, **_: int) -> list[PlannerRun]:
        self.user_ids.append(user_id)
        if trip_id == 404:
            raise TripNotFoundError()
        return [self.run]

    def get_latest_trip_run(self, *, trip_id: int, user_id: int) -> PlannerRun | None:
        self.user_ids.append(user_id)
        return self.run

    def get_latest_accepted_trip_run(self, *, trip_id: int, user_id: int) -> PlannerRun | None:
        self.user_ids.append(user_id)
        return make_run(status=PlannerRunStatus.ACCEPTED)

    def accept_run(self, *, planner_run_id: int, user_id: int) -> PlannerRun | None:
        self.user_ids.append(user_id)
        return make_run(status=PlannerRunStatus.ACCEPTED)

    def reject_run(self, *, planner_run_id: int, user_id: int) -> PlannerRun | None:
        self.user_ids.append(user_id)
        return make_run(status=PlannerRunStatus.REJECTED)

    def update_evidence(self, *, planner_run_id: int, user_id: int, **_: object) -> PlannerRun | None:
        self.user_ids.append(user_id)
        if planner_run_id == 503:
            raise SQLAlchemyError("database details")
        return make_run(feasibility_score=90)

    def rollback(self) -> None:
        self.rolled_back = True


def install(service: FakePlannerRunService) -> None:
    app.dependency_overrides[get_current_active_user] = lambda: SimpleNamespace(id=7)
    app.dependency_overrides[get_planner_run_service] = lambda: service


CREATE_PAYLOAD = {
    "trip_id": 22, "input_snapshot": {}, "itinerary_snapshot": {},
    "feasibility_snapshot": {}, "recommendations_snapshot": {},
    "optimization_snapshot": {},
}
EVIDENCE_PAYLOAD = {
    "feasibility_score": 90, "feasibility_snapshot": {},
    "recommendations_snapshot": {}, "optimization_snapshot": {},
}


def test_routes_require_authentication() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/planner-runs").status_code == 401
        assert client.post("/api/v1/planner-runs", json=CREATE_PAYLOAD).status_code == 401


def test_create_uses_auth_user_and_denies_cross_user_trip() -> None:
    service = FakePlannerRunService()
    install(service)
    try:
        with TestClient(app) as client:
            created = client.post("/api/v1/planner-runs", json=CREATE_PAYLOAD)
            denied = client.post("/api/v1/planner-runs", json={**CREATE_PAYLOAD, "trip_id": 404})
    finally:
        app.dependency_overrides.clear()
    assert created.status_code == 201 and created.json()["user_id"] == 7
    assert denied.status_code == 404 and service.user_ids == [7, 7]


def test_owned_retrieve_list_and_trip_queries() -> None:
    service = FakePlannerRunService()
    install(service)
    try:
        with TestClient(app) as client:
            responses = [
                client.get("/api/v1/planner-runs"), client.get("/api/v1/planner-runs/1"),
                client.get("/api/v1/trips/22/planner-runs"),
                client.get("/api/v1/trips/22/planner-runs/latest"),
                client.get("/api/v1/trips/22/planner-runs/latest-accepted"),
            ]
            hidden = client.get("/api/v1/planner-runs/404")
            denied = client.get("/api/v1/trips/404/planner-runs")
    finally:
        app.dependency_overrides.clear()
    assert all(response.status_code == 200 for response in responses)
    assert responses[-1].json()["status"] == "accepted"
    assert hidden.status_code == 404 and denied.status_code == 404
    assert set(service.user_ids) == {7}


def test_accept_reject_evidence_and_persistence_rollback() -> None:
    service = FakePlannerRunService()
    install(service)
    try:
        with TestClient(app) as client:
            accepted = client.post("/api/v1/planner-runs/1/accept")
            rejected = client.post("/api/v1/planner-runs/1/reject")
            evidence = client.patch("/api/v1/planner-runs/1/evidence", json=EVIDENCE_PAYLOAD)
            failed = client.patch("/api/v1/planner-runs/503/evidence", json=EVIDENCE_PAYLOAD)
    finally:
        app.dependency_overrides.clear()
    assert accepted.json()["status"] == "accepted"
    assert rejected.json()["status"] == "rejected"
    assert evidence.json()["feasibility_score"] == 90
    assert failed.status_code == 503
    assert failed.json() == {"detail": "Planner run service is unavailable"}
    assert service.rolled_back is True
