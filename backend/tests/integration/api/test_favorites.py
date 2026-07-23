from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_active_user,
    get_current_user,
    get_favorite_service,
)
from app.core.exceptions import (
    DestinationNotFoundError,
    FavoriteIntegrityError,
    FavoritePersistenceError,
)
from app.main import app
from app.schemas.favorite import (
    FavoriteCheckResponse,
    FavoriteDestinationItem,
    FavoriteListResponse,
    FavoriteRead,
)


def favorite_response() -> FavoriteRead:
    return FavoriteRead(
        id=11,
        destination=FavoriteDestinationItem(
            id=7,
            slug="leptis-magna",
            name_ar="لبدة الكبرى",
            name_en="Leptis Magna",
            municipality="Al Khums",
            region="Tripolitania",
            category=None,
            primary_media_url="/media/leptis.jpg",
            is_featured=True,
        ),
        created_at=datetime.now(UTC),
    )


class FakeFavoriteService:
    def __init__(self) -> None:
        self.favorite = favorite_response()
        self.error = None

    def _raise(self) -> None:
        if self.error is not None:
            raise self.error

    def add_favorite(self, user_id: int, destination_id: int) -> FavoriteRead:
        self._raise()
        return self.favorite

    def delete_favorite(self, user_id: int, destination_id: int) -> None:
        self._raise()

    def list_favorites(self, *, user_id: int, skip: int, limit: int) -> FavoriteListResponse:
        self._raise()
        return FavoriteListResponse(items=[self.favorite], total=1, skip=skip, limit=limit)

    def check_favorite(self, user_id: int, destination_id: int) -> FavoriteCheckResponse:
        self._raise()
        return FavoriteCheckResponse(destination_id=destination_id, is_favorite=True)


def request(
    service: FakeFavoriteService,
    test_user,
    method: str,
    path: str,
    *,
    authenticated: bool = True,
    **kwargs,
):
    app.dependency_overrides[get_favorite_service] = lambda: service
    if authenticated:
        app.dependency_overrides[get_current_active_user] = lambda: test_user
    try:
        with TestClient(app) as client:
            return client.request(method, path, **kwargs)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("method", "path", "expected_status"),
    [
        ("POST", "/api/v1/favorites/7", 200),
        ("DELETE", "/api/v1/favorites/7", 204),
        ("GET", "/api/v1/favorites", 200),
        ("GET", "/api/v1/favorites/check/7", 200),
    ],
)
def test_favorite_endpoints_are_protected(test_user, method, path, expected_status) -> None:
    service = FakeFavoriteService()
    unauthorized = request(
        service,
        test_user,
        method,
        path,
        authenticated=False,
    )
    assert unauthorized.status_code == 401
    assert unauthorized.headers["www-authenticate"] == "Bearer"

    authorized = request(service, test_user, method, path)
    assert authorized.status_code == expected_status


def test_add_is_idempotent_and_returns_destination(test_user) -> None:
    service = FakeFavoriteService()
    first = request(service, test_user, "POST", "/api/v1/favorites/7")
    second = request(service, test_user, "POST", "/api/v1/favorites/7")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["destination"]["slug"] == "leptis-magna"


def test_delete_twice_is_idempotent_and_has_no_body(test_user) -> None:
    service = FakeFavoriteService()
    first = request(service, test_user, "DELETE", "/api/v1/favorites/7")
    second = request(service, test_user, "DELETE", "/api/v1/favorites/7")
    assert first.status_code == second.status_code == 204
    assert first.content == second.content == b""


def test_list_pagination_and_check(test_user) -> None:
    service = FakeFavoriteService()
    listed = request(
        service,
        test_user,
        "GET",
        "/api/v1/favorites",
        params={"skip": 5, "limit": 10},
    )
    assert listed.status_code == 200
    assert listed.json()["skip"] == 5
    assert listed.json()["limit"] == 10
    assert listed.json()["total"] == 1

    checked = request(service, test_user, "GET", "/api/v1/favorites/check/7")
    assert checked.json() == {"destination_id": 7, "is_favorite": True}


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (DestinationNotFoundError(), 404),
        (FavoriteIntegrityError(), 409),
        (FavoritePersistenceError(), 500),
    ],
)
def test_favorite_error_mapping(test_user, error, status_code) -> None:
    service = FakeFavoriteService()
    service.error = error
    response = request(service, test_user, "POST", "/api/v1/favorites/7")
    assert response.status_code == status_code
    if status_code == 500:
        assert response.json()["detail"] == "Favorite service could not complete the request"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("DELETE", "/api/v1/favorites/7"),
        ("GET", "/api/v1/favorites"),
        ("GET", "/api/v1/favorites/check/7"),
    ],
)
def test_persistence_errors_are_generic_on_all_endpoints(test_user, method, path) -> None:
    service = FakeFavoriteService()
    service.error = FavoritePersistenceError()
    response = request(service, test_user, method, path)
    assert response.status_code == 500
    assert response.json()["detail"] == "Favorite service could not complete the request"


def test_inactive_user_is_rejected_by_real_active_dependency(inactive_user) -> None:
    service = FakeFavoriteService()
    app.dependency_overrides[get_favorite_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: inactive_user
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/favorites")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_invalid_path_and_pagination_return_422(test_user) -> None:
    service = FakeFavoriteService()
    assert request(service, test_user, "POST", "/api/v1/favorites/0").status_code == 422
    assert request(
        service,
        test_user,
        "GET",
        "/api/v1/favorites",
        params={"limit": 101},
    ).status_code == 422
    assert request(
        service,
        test_user,
        "GET",
        "/api/v1/favorites",
        params={"limit": 100},
    ).status_code == 200
