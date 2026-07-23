from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user, get_current_user, get_trip_service
from app.core.exceptions import (
    DestinationUnavailableForTripError,
    DuplicateTripDestinationError,
    InvalidTripDateRangeError,
    TripConcurrentModificationError,
    TripItemLimitExceededError,
    TripNotFoundError,
    TripPersistenceError,
)
from app.main import app
from app.models.trip import TripStatus, TripVisibility
from app.schemas.trip import (
    TripDetailResponse,
    TripDestinationSummary,
    TripItemResponse,
    TripListResponse,
    TripSummaryResponse,
)


NOW = datetime.now(UTC)


def detail() -> TripDetailResponse:
    item = TripItemResponse(
        id=11,
        destination=TripDestinationSummary(id=7, slug="leptis", name_ar=None, name_en="Leptis"),
        day_number=1,
        visit_date=date(2026, 9, 1),
        start_time=None,
        duration_minutes=120,
        sort_order=0,
        notes=None,
        created_at=NOW,
        updated_at=NOW,
    )
    return TripDetailResponse(
        id=3,
        title="Libya",
        description=None,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 3),
        status=TripStatus.DRAFT,
        visibility=TripVisibility.PRIVATE,
        version=1,
        duration_days=3,
        item_count=1,
        items=[item],
        created_at=NOW,
        updated_at=NOW,
    )


class FakeTripService:
    def __init__(self) -> None:
        self.trip = detail()
        self.error = None

    def _raise(self):
        if self.error:
            raise self.error

    def create_trip(self, user_id, payload): self._raise(); return self.trip
    def list_user_trips(self, user_id, skip, limit):
        self._raise()
        summary = TripSummaryResponse(**self.trip.model_dump(exclude={"items"}))
        return TripListResponse(items=[summary], total=1, skip=skip, limit=limit)
    def get_trip(self, user_id, trip_id): self._raise(); return self.trip
    def update_trip(self, user_id, trip_id, payload): self._raise(); return self.trip
    def delete_trip(self, user_id, trip_id): self._raise()
    def add_trip_item(self, user_id, trip_id, payload): self._raise(); return self.trip.items[0]
    def update_trip_item(self, user_id, trip_id, item_id, payload): self._raise(); return self.trip.items[0]
    def delete_trip_item(self, user_id, trip_id, item_id): self._raise()
    def reorder_trip_items(self, user_id, trip_id, payload): self._raise(); return self.trip


def request(service, user, method, path, authenticated=True, **kwargs):
    app.dependency_overrides[get_trip_service] = lambda: service
    if authenticated:
        app.dependency_overrides[get_current_active_user] = lambda: user
    try:
        with TestClient(app) as client:
            return client.request(method, path, **kwargs)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("method", "path", "body", "status_code"),
    [
        ("POST", "/api/v1/trips", {"title": "Libya"}, 201),
        ("GET", "/api/v1/trips", None, 200),
        ("GET", "/api/v1/trips/3", None, 200),
        ("PATCH", "/api/v1/trips/3", {"title": "New"}, 200),
        ("DELETE", "/api/v1/trips/3", None, 204),
        ("POST", "/api/v1/trips/3/items", {"destination_id": 7}, 201),
        ("PATCH", "/api/v1/trips/3/items/11", {"notes": "Visit"}, 200),
        ("DELETE", "/api/v1/trips/3/items/11", None, 204),
        ("PUT", "/api/v1/trips/3/items/reorder", {"expected_version": 1, "items": [{"item_id": 11, "day_number": 1}]}, 200),
    ],
)
def test_all_trip_routes_require_authentication(test_user, method, path, body, status_code):
    service = FakeTripService()
    unauthorized = request(service, test_user, method, path, False, json=body)
    assert unauthorized.status_code == 401
    assert unauthorized.headers["www-authenticate"] == "Bearer"
    authorized = request(service, test_user, method, path, json=body)
    assert authorized.status_code == status_code
    if status_code == 204:
        assert authorized.content == b""


def test_list_pagination_and_user_isolation_not_found(test_user) -> None:
    service = FakeTripService()
    response = request(service, test_user, "GET", "/api/v1/trips", params={"skip": 5, "limit": 10})
    assert response.json()["skip"] == 5 and response.json()["limit"] == 10
    service.error = TripNotFoundError()
    assert request(service, test_user, "GET", "/api/v1/trips/99").status_code == 404


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (InvalidTripDateRangeError(), 422),
        (DestinationUnavailableForTripError(), 422),
        (DuplicateTripDestinationError(), 409),
        (TripConcurrentModificationError(), 409),
        (TripItemLimitExceededError(), 422),
        (TripPersistenceError(), 500),
    ],
)
def test_domain_error_mapping(test_user, error, status_code) -> None:
    service = FakeTripService()
    service.error = error
    response = request(service, test_user, "POST", "/api/v1/trips", json={"title": "Libya"})
    assert response.status_code == status_code
    if status_code == 500:
        assert response.json()["detail"] == "Trip service could not complete the request"


def test_validation_and_inactive_user(test_user, inactive_user) -> None:
    service = FakeTripService()
    assert request(service, test_user, "POST", "/api/v1/trips", json={"title": "   "}).status_code == 422
    assert request(service, test_user, "GET", "/api/v1/trips", params={"limit": 101}).status_code == 422
    assert request(service, test_user, "POST", "/api/v1/trips/3/items", json={"destination_id": 0}).status_code == 422
    oversized_reorder = {
        "expected_version": 1,
        "items": [
            {"item_id": index + 1, "day_number": 1}
            for index in range(101)
        ],
    }
    assert request(
        service,
        test_user,
        "PUT",
        "/api/v1/trips/3/items/reorder",
        json=oversized_reorder,
    ).status_code == 422

    app.dependency_overrides[get_trip_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: inactive_user
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/trips")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_openapi_marks_every_trip_operation_as_bearer_protected() -> None:
    schema = app.openapi()
    operations = [
        operation
        for path, path_data in schema["paths"].items()
        if path.startswith("/api/v1/trips")
        for operation in path_data.values()
        if isinstance(operation, dict) and "responses" in operation
    ]
    assert len(operations) == 9
    assert all(operation.get("security") for operation in operations)


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/api/v1/trips", None),
        ("GET", "/api/v1/trips/3", None),
        ("PATCH", "/api/v1/trips/3", {"title": "New"}),
        ("DELETE", "/api/v1/trips/3", None),
        ("POST", "/api/v1/trips/3/items", {"destination_id": 7}),
        ("PATCH", "/api/v1/trips/3/items/11", {"notes": "x"}),
        ("DELETE", "/api/v1/trips/3/items/11", None),
        ("PUT", "/api/v1/trips/3/items/reorder", {"expected_version": 1, "items": [{"item_id": 11, "day_number": 1}]}),
    ],
)
def test_persistence_failure_is_generic_for_every_operation(test_user, method, path, body) -> None:
    service = FakeTripService()
    service.error = TripPersistenceError()
    response = request(service, test_user, method, path, json=body)
    assert response.status_code == 500
    assert response.json()["detail"] == "Trip service could not complete the request"
