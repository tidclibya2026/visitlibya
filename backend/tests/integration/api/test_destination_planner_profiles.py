from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_destination_planner_profile_service,
    require_content_admin,
)
from app.core.exceptions import (
    DestinationNotFoundError,
    DestinationPlannerProfileConflictError,
    DestinationPlannerProfileNotFoundError,
    DestinationPlannerProfilePersistenceError,
)
from app.main import app
from app.models.destination_planner_profile import (
    DestinationPlannerProfile,
    PlannerAccessStatus,
    PlannerRoadAccess,
    PlannerRoadCondition,
    PlannerRoadSurface,
    PlannerVerificationStatus,
)
from app.schemas.destination_planner_profile import (
    DestinationPlannerProfileCreate,
    DestinationPlannerProfileUpdate,
)


def make_profile(destination_id: int = 7) -> DestinationPlannerProfile:
    now = datetime.now(UTC)
    return DestinationPlannerProfile(
        id=3,
        destination_id=destination_id,
        opening_hours={},
        opening_hours_timezone="Africa/Tripoli",
        access_status=PlannerAccessStatus.UNKNOWN,
        road_access=PlannerRoadAccess.UNKNOWN,
        road_surface=PlannerRoadSurface.UNKNOWN,
        road_condition=PlannerRoadCondition.UNKNOWN,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=PlannerVerificationStatus.UNVERIFIED,
        created_at=now,
        updated_at=now,
    )


class FakeDestinationPlannerProfileService:
    def __init__(self) -> None:
        self.profile = make_profile()
        self.created_payload: DestinationPlannerProfileCreate | None = None
        self.updated_destination_id: int | None = None

    def get_profile(self, destination_id: int) -> DestinationPlannerProfile:
        if destination_id == 404:
            raise DestinationPlannerProfileNotFoundError()
        if destination_id == 503:
            raise DestinationPlannerProfilePersistenceError()
        return self.profile

    def create_profile(
        self,
        payload: DestinationPlannerProfileCreate,
    ) -> DestinationPlannerProfile:
        self.created_payload = payload
        if payload.destination_id == 404:
            raise DestinationNotFoundError()
        if payload.destination_id == 409:
            raise DestinationPlannerProfileConflictError()
        self.profile.destination_id = payload.destination_id
        self.profile.planner_priority = payload.planner_priority
        return self.profile

    def update_profile(
        self,
        *,
        destination_id: int,
        payload: DestinationPlannerProfileUpdate,
    ) -> DestinationPlannerProfile:
        self.updated_destination_id = destination_id
        if destination_id == 404:
            raise DestinationPlannerProfileNotFoundError()
        if payload.planner_priority is not None:
            self.profile.planner_priority = payload.planner_priority
        return self.profile


def install_overrides(service: FakeDestinationPlannerProfileService) -> None:
    app.dependency_overrides[get_destination_planner_profile_service] = lambda: service
    app.dependency_overrides[require_content_admin] = lambda: SimpleNamespace(id=99)


def test_profile_routes_require_authentication() -> None:
    with TestClient(app) as client:
        get_response = client.get("/api/v1/destinations/7/planner-profile")
        post_response = client.post(
            "/api/v1/destinations/7/planner-profile",
            json={},
        )
        patch_response = client.patch(
            "/api/v1/destinations/7/planner-profile",
            json={"planner_priority": 70},
        )
    assert {get_response.status_code, post_response.status_code, patch_response.status_code} == {401}


def test_get_profile_success_and_missing() -> None:
    service = FakeDestinationPlannerProfileService()
    install_overrides(service)
    try:
        with TestClient(app) as client:
            found = client.get("/api/v1/destinations/7/planner-profile")
            missing = client.get("/api/v1/destinations/404/planner-profile")
    finally:
        app.dependency_overrides.clear()
    assert found.status_code == 200
    assert found.json()["destination_id"] == 7
    assert missing.status_code == 404


def test_create_uses_route_destination_id_and_rejects_body_id() -> None:
    service = FakeDestinationPlannerProfileService()
    install_overrides(service)
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/destinations/12/planner-profile",
                json={"planner_priority": 80},
            )
            duplicate_id = client.post(
                "/api/v1/destinations/12/planner-profile",
                json={"destination_id": 99},
            )
    finally:
        app.dependency_overrides.clear()
    assert created.status_code == 201
    assert service.created_payload is not None
    assert service.created_payload.destination_id == 12
    assert duplicate_id.status_code == 422


def test_create_maps_missing_destination_and_conflict() -> None:
    service = FakeDestinationPlannerProfileService()
    install_overrides(service)
    try:
        with TestClient(app) as client:
            missing = client.post("/api/v1/destinations/404/planner-profile", json={})
            conflict = client.post("/api/v1/destinations/409/planner-profile", json={})
    finally:
        app.dependency_overrides.clear()
    assert missing.status_code == 404
    assert conflict.status_code == 409


def test_patch_uses_route_id_and_validates_payload() -> None:
    service = FakeDestinationPlannerProfileService()
    install_overrides(service)
    try:
        with TestClient(app) as client:
            updated = client.patch(
                "/api/v1/destinations/7/planner-profile",
                json={"planner_priority": 75},
            )
            invalid = client.patch(
                "/api/v1/destinations/7/planner-profile",
                json={"planner_priority": 101},
            )
    finally:
        app.dependency_overrides.clear()
    assert updated.status_code == 200
    assert updated.json()["planner_priority"] == 75
    assert service.updated_destination_id == 7
    assert invalid.status_code == 422


def test_verified_at_is_not_client_writeable() -> None:
    service = FakeDestinationPlannerProfileService()
    install_overrides(service)
    try:
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/destinations/7/planner-profile",
                json={"verified_at": "2026-08-26T12:00:00Z"},
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_persistence_failure_is_sanitized_as_service_unavailable() -> None:
    service = FakeDestinationPlannerProfileService()
    install_overrides(service)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/destinations/503/planner-profile")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Destination planner profile service is unavailable"
    }
