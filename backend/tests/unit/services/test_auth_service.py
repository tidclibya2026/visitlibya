from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    AuthenticationPersistenceError,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    RegistrationConflictError,
    UsernameAlreadyRegisteredError,
)
from app.core.security import verify_password
from app.schemas.auth import UserRegistrationRequest
from app.services.auth import AuthService


def make_service(user=None):
    session = MagicMock()
    session.is_active = True
    repository = MagicMock()
    repository.get_by_login_identifier.return_value = user
    repository.get_by_id.return_value = user
    return AuthService(session, repository), session, repository


def registration_payload(**overrides) -> UserRegistrationRequest:
    values = {
        "full_name": "New Traveler",
        "email": "NEW.TRAVELER@EXAMPLE.COM",
        "username": "New.Traveler",
        "password": "SecurePassword123!",
    }
    values.update(overrides)
    return UserRegistrationRequest(**values)


@pytest.mark.parametrize("identifier", ["traveler@example.com", "traveler"])
def test_login_by_email_or_username(identifier, test_user, monkeypatch) -> None:
    service, _, repository = make_service(test_user)
    monkeypatch.setattr("app.services.auth.verify_password", lambda plain, hashed: True)
    monkeypatch.setattr("app.services.auth.create_access_token", lambda subject: "signed-token")
    response = service.login(identifier, "correct-password")
    repository.get_by_login_identifier.assert_called_once_with(identifier)
    assert response.access_token == "signed-token"
    assert response.token_type == "bearer"
    assert response.expires_in == 1800


def test_login_strips_identifier_without_changing_password(test_user, monkeypatch) -> None:
    service, _, repository = make_service(test_user)
    password_check = MagicMock(return_value=True)
    monkeypatch.setattr("app.services.auth.verify_password", password_check)
    monkeypatch.setattr("app.services.auth.create_access_token", lambda subject: "signed-token")
    service.login("  traveler  ", " password-with-spaces ")
    repository.get_by_login_identifier.assert_called_once_with("traveler")
    assert password_check.call_args.args[0] == " password-with-spaces "


def test_wrong_password_and_unknown_user_share_generic_error(test_user, monkeypatch) -> None:
    monkeypatch.setattr("app.services.auth.verify_password", lambda plain, hashed: False)
    known_service, _, _ = make_service(test_user)
    unknown_service, _, _ = make_service(None)
    with pytest.raises(InvalidCredentialsError) as known_error:
        known_service.login("traveler", "wrong")
    with pytest.raises(InvalidCredentialsError) as unknown_error:
        unknown_service.login("unknown", "wrong")
    assert str(known_error.value) == str(unknown_error.value)


def test_inactive_user_checked_after_password(inactive_user, monkeypatch) -> None:
    service, _, _ = make_service(inactive_user)
    monkeypatch.setattr("app.services.auth.verify_password", lambda plain, hashed: True)
    with pytest.raises(InactiveUserError):
        service.login("inactive", "correct-password")


def test_get_user_by_id_and_missing_user(test_user) -> None:
    service, _, _ = make_service(test_user)
    assert service.get_user_by_id(1) is test_user
    missing_service, _, _ = make_service(None)
    with pytest.raises(InvalidTokenError):
        missing_service.get_user_by_id(999)


def test_repository_failure_maps_to_persistence_error() -> None:
    service, _, repository = make_service()
    repository.get_by_login_identifier.side_effect = SQLAlchemyError("database down")
    with pytest.raises(AuthenticationPersistenceError):
        service.login("traveler", "password")


def test_register_normalizes_identity_hashes_password_and_commits() -> None:
    service, session, repository = make_service()
    repository.get_by_email.return_value = None
    repository.get_by_username.return_value = None

    user = service.register(registration_payload())

    repository.get_by_email.assert_called_once_with("new.traveler@example.com")
    repository.get_by_username.assert_called_once_with("new.traveler")
    repository.create.assert_called_once_with(user)
    session.commit.assert_called_once_with()
    assert user.full_name == "New Traveler"
    assert user.email == "new.traveler@example.com"
    assert user.username == "new.traveler"
    assert verify_password("SecurePassword123!", user.hashed_password)
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.roles == []


@pytest.mark.parametrize(
    ("conflicting_field", "expected_error"),
    [
        ("email", EmailAlreadyRegisteredError),
        ("username", UsernameAlreadyRegisteredError),
    ],
)
def test_register_rejects_existing_identity(
    conflicting_field,
    expected_error,
    test_user,
) -> None:
    service, session, repository = make_service()
    repository.get_by_email.return_value = (
        test_user if conflicting_field == "email" else None
    )
    repository.get_by_username.return_value = (
        test_user if conflicting_field == "username" else None
    )

    with pytest.raises(expected_error):
        service.register(registration_payload())

    repository.create.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_register_maps_unique_constraint_race_to_conflict() -> None:
    service, session, repository = make_service()
    repository.get_by_email.return_value = None
    repository.get_by_username.return_value = None
    repository.create.side_effect = IntegrityError("insert", {}, Exception("unique"))

    with pytest.raises(RegistrationConflictError):
        service.register(registration_payload())

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_register_maps_database_failure_to_safe_persistence_error() -> None:
    service, session, repository = make_service()
    repository.get_by_email.side_effect = SQLAlchemyError("database details")

    with pytest.raises(AuthenticationPersistenceError) as raised:
        service.register(registration_payload())

    assert "database details" not in str(raised.value)
    session.rollback.assert_called_once_with()


def test_registered_password_can_be_used_by_login(monkeypatch) -> None:
    service, _, repository = make_service()
    repository.get_by_email.return_value = None
    repository.get_by_username.return_value = None
    user = service.register(registration_payload())
    repository.reset_mock()
    repository.get_by_login_identifier.return_value = user
    monkeypatch.setattr("app.services.auth.create_access_token", lambda subject: "token")

    response = service.login(user.email, "SecurePassword123!")

    assert response.access_token == "token"
