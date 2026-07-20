from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationPersistenceError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.security import create_access_token
from app.main import app
from app.schemas.auth import TokenResponse
from app.models.role import Role


class FakeAuthService:
    def __init__(self, user) -> None:
        self.user = user
        self.login_error = None
        self.user_error = None

    def login(self, identifier: str, password: str) -> TokenResponse:
        if self.login_error is not None:
            raise self.login_error
        return TokenResponse(access_token=create_access_token(self.user.id), expires_in=1800)

    def get_user_by_id(self, user_id: int):
        if self.user_error is not None:
            raise self.user_error
        if self.user is None or self.user.id != user_id:
            raise InvalidTokenError()
        return self.user


def request_with_service(service, method: str, path: str, **kwargs):
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        with TestClient(app) as client:
            return client.request(method, path, **kwargs)
    finally:
        app.dependency_overrides.clear()


def test_successful_login(test_user) -> None:
    response = request_with_service(
        FakeAuthService(test_user),
        "POST",
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "correct-password"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == 1800


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [(InvalidCredentialsError(), 401), (InactiveUserError(), 403), (AuthenticationPersistenceError(), 500)],
)
def test_login_error_mapping(test_user, error, expected_status) -> None:
    service = FakeAuthService(test_user)
    service.login_error = error
    response = request_with_service(
        service,
        "POST",
        "/api/v1/auth/login",
        data={"username": "traveler", "password": "wrong-password"},
    )
    assert response.status_code == expected_status
    if expected_status == 401:
        assert response.headers["www-authenticate"] == "Bearer"


def test_me_requires_bearer_token(test_user) -> None:
    response = request_with_service(FakeAuthService(test_user), "GET", "/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_returns_safe_current_user(test_user) -> None:
    test_user.roles = [Role(id=1, name="Traveler", code="traveler")]
    token = create_access_token(test_user.id)
    response = request_with_service(
        FakeAuthService(test_user),
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "traveler@example.com",
        "username": "traveler",
        "full_name": "Test Traveler",
        "is_active": True,
        "is_superuser": False,
        "roles": ["Traveler"],
    }
    assert "hashed_password" not in response.json()


@pytest.mark.parametrize("token_kind", ["expired", "wrong_signature", "invalid_subject"])
def test_me_rejects_invalid_tokens(test_user, token_kind) -> None:
    if token_kind == "expired":
        token = create_access_token(test_user.id, expires_delta=timedelta(seconds=-1))
    elif token_kind == "wrong_signature":
        token = jwt.encode(
            {"sub": str(test_user.id), "exp": 4102444800},
            "wrong-signature-secret-that-is-long-enough",
            algorithm="HS256",
        )
    else:
        token = jwt.encode(
            {"sub": "invalid", "exp": 4102444800},
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        )
    response = request_with_service(
        FakeAuthService(test_user),
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_rejects_unknown_or_inactive_user(test_user, inactive_user) -> None:
    token = create_access_token(test_user.id)
    missing_response = request_with_service(
        FakeAuthService(None),
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert missing_response.status_code == 401

    inactive_token = create_access_token(inactive_user.id)
    inactive_response = request_with_service(
        FakeAuthService(inactive_user),
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {inactive_token}"},
    )
    assert inactive_response.status_code == 403


def test_me_rejects_token_without_exp(test_user) -> None:
    token = jwt.encode(
        {"sub": str(test_user.id)},
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )
    response = request_with_service(
        FakeAuthService(test_user),
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
