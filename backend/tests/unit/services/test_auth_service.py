from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import (
    AuthenticationPersistenceError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.services.auth import AuthService


def make_service(user=None):
    session = MagicMock()
    session.is_active = True
    repository = MagicMock()
    repository.get_by_login_identifier.return_value = user
    repository.get_by_id.return_value = user
    return AuthService(session, repository), session, repository


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
