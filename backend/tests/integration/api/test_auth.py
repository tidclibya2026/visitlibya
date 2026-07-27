from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationPersistenceError,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    RegistrationConflictError,
    UsernameAlreadyRegisteredError,
)
from app.core.security import create_access_token
from app.main import app
from app.schemas.auth import TokenResponse, UserRegistrationRequest
from app.models.role import Role


class FakeAuthService:
    def __init__(self, user) -> None:
        self.user = user
        self.login_error = None
        self.registration_error = None
        self.user_error = None

    def register(self, payload: UserRegistrationRequest):
        if self.registration_error is not None:
            raise self.registration_error
        self.user.full_name = payload.full_name
        self.user.email = str(payload.email)
        self.user.username = payload.username
        self.user.is_active = True
        self.user.is_superuser = False
        self.user.roles = []
        return self.user

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


def test_successful_registration_returns_only_safe_normal_user_fields(test_user) -> None:
    response = request_with_service(
        FakeAuthService(test_user),
        "POST",
        "/api/v1/auth/register",
        json={
            "full_name": "New Traveler",
            "email": "NEW@EXAMPLE.COM",
            "username": "NewTraveler",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "email": "new@example.com",
        "username": "newtraveler",
        "full_name": "New Traveler",
        "is_active": True,
        "is_superuser": False,
    }
    assert "hashed_password" not in response.json()
    assert "password" not in response.json()
    assert "roles" not in response.json()


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (
            EmailAlreadyRegisteredError(),
            409,
            "An account already exists with this email address",
        ),
        (
            UsernameAlreadyRegisteredError(),
            409,
            "This username is already in use",
        ),
        (
            RegistrationConflictError(),
            409,
            "An account with this email or username already exists",
        ),
        (
            AuthenticationPersistenceError(),
            500,
            "Authentication service is unavailable",
        ),
    ],
)
def test_registration_error_mapping(
    test_user,
    error,
    expected_status,
    expected_detail,
) -> None:
    service = FakeAuthService(test_user)
    service.registration_error = error
    response = request_with_service(
        service,
        "POST",
        "/api/v1/auth/register",
        json={
            "full_name": "New Traveler",
            "email": "new@example.com",
            "username": "newtraveler",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


@pytest.mark.parametrize(
    "origin",
    ["http://127.0.0.1:5500", "http://localhost:5500"],
)
def test_auth_login_cors_allows_local_frontend_origins(origin) -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"password": "weak-password"},
        {"username": "invalid username"},
        {"full_name": "   "},
    ],
)
def test_registration_validation_rejects_invalid_fields(test_user, overrides) -> None:
    payload = {
        "full_name": "New Traveler",
        "email": "new@example.com",
        "username": "newtraveler",
        "password": "SecurePassword123!",
        **overrides,
    }
    response = request_with_service(
        FakeAuthService(test_user),
        "POST",
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code == 422


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
