from unittest.mock import MagicMock

from app.models.destination_planner_profile import (
    DestinationPlannerProfile,
)
from app.repositories.destination_planner_profile import (
    DestinationPlannerProfileRepository,
)


def test_repository_adds_profile():
    session = MagicMock()
    repository = DestinationPlannerProfileRepository(session)

    profile = DestinationPlannerProfile(destination_id=7)

    repository.create_profile(profile)

    session.add.assert_called_once_with(profile)


def test_repository_gets_profile_by_destination_id():
    session = MagicMock()
    profile = DestinationPlannerProfile(destination_id=7)
    session.scalar.return_value = profile

    repository = DestinationPlannerProfileRepository(session)

    result = repository.get_by_destination_id(7)

    assert result is profile
    session.scalar.assert_called_once()


def test_repository_checks_destination_exists():
    session = MagicMock()
    session.scalar.return_value = 7

    repository = DestinationPlannerProfileRepository(session)

    assert repository.destination_exists(7) is True


def test_repository_checks_profile_exists():
    session = MagicMock()
    session.scalar.return_value = 22

    repository = DestinationPlannerProfileRepository(session)

    assert repository.profile_exists_for_destination(7) is True


def test_repository_returns_false_when_profile_missing():
    session = MagicMock()
    session.scalar.return_value = None

    repository = DestinationPlannerProfileRepository(session)

    assert repository.profile_exists_for_destination(7) is False
