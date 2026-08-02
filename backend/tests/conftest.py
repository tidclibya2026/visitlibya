import os

import pytest


os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-jwt-secret-key-that-is-at-least-32-characters",
)


@pytest.fixture(scope="session")
def password_hash_value() -> str:
    from app.core.security import hash_password

    return hash_password("CorrectHorseBatteryStaple!")


@pytest.fixture
def test_user(password_hash_value: str):
    from app.models.user import User

    return User(
        id=1,
        full_name="Test Traveler",
        email="traveler@example.com",
        username="traveler",
        hashed_password=password_hash_value,
        is_active=True,
        is_superuser=False,
        roles=[],
    )


@pytest.fixture
def inactive_user(password_hash_value: str):
    from app.models.user import User

    return User(
        id=2,
        full_name="Inactive Traveler",
        email="inactive@example.com",
        username="inactive",
        hashed_password=password_hash_value,
        is_active=False,
        is_superuser=False,
        roles=[],
    )


@pytest.fixture
def admin_user(password_hash_value: str):
    from app.models.role import Role
    from app.models.user import User

    role = Role(id=1, name="Content administrator", code="content_admin", is_active=True)
    return User(
        id=3, full_name="Content Administrator", email="admin@example.test",
        username="content-admin", hashed_password=password_hash_value,
        is_active=True, is_superuser=False, roles=[role],
    )


@pytest.fixture
def access_token_factory():
    from app.core.security import create_access_token

    return create_access_token
