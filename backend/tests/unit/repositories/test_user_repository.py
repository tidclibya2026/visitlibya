from unittest.mock import MagicMock

from app.models.user import User
from app.repositories.user import UserRepository


def test_user_repository_lookups() -> None:
    session = MagicMock()
    user = User(id=1, full_name="Traveler", email="t@example.com", username="traveler", hashed_password="hash")
    session.scalar.return_value = user
    repository = UserRepository(session)

    assert repository.get_by_id(1) is user
    assert "users.id" in str(session.scalar.call_args.args[0])
    assert repository.get_by_email("t@example.com") is user
    assert "users.email" in str(session.scalar.call_args.args[0])
    assert repository.get_by_username("traveler") is user
    assert "users.username" in str(session.scalar.call_args.args[0])


def test_login_identifier_selects_email_or_username() -> None:
    repository = UserRepository(MagicMock())
    repository.get_by_email = MagicMock(return_value=None)
    repository.get_by_username = MagicMock(return_value=None)
    assert repository.get_by_login_identifier("t@example.com") is None
    repository.get_by_email.assert_called_once_with("t@example.com")
    assert repository.get_by_login_identifier("traveler") is None
    repository.get_by_username.assert_called_once_with("traveler")


def test_not_found_returns_none() -> None:
    session = MagicMock()
    session.scalar.return_value = None
    assert UserRepository(session).get_by_id(999) is None


def test_create_adds_and_flushes_user() -> None:
    session = MagicMock()
    repository = UserRepository(session)
    user = User(
        full_name="New Traveler",
        email="new@example.com",
        username="newtraveler",
        hashed_password="hash",
    )

    assert repository.create(user) is user
    session.add.assert_called_once_with(user)
    session.flush.assert_called_once_with()
