from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    DestinationNotFoundError,
    DestinationPlannerProfileConflictError,
    DestinationPlannerProfileIntegrityError,
    DestinationPlannerProfileNotFoundError,
    DestinationPlannerProfilePersistenceError,
    DestinationPlannerProfileValidationError,
)
from app.models.destination_planner_profile import (
    DestinationPlannerProfile,
    PlannerVerificationStatus,
)
from app.schemas.destination_planner_profile import (
    DestinationPlannerProfileCreate,
    DestinationPlannerProfileUpdate,
)
from app.services.destination_planner_profile import (
    DestinationPlannerProfileService,
)


def build_service():
    session = MagicMock()
    repository = MagicMock()

    service = DestinationPlannerProfileService(
        session=session,
        repository=repository,
    )

    return service, session, repository


def test_create_profile_success():
    service, session, repository = build_service()

    repository.destination_exists.return_value = True
    repository.profile_exists_for_destination.return_value = False

    payload = DestinationPlannerProfileCreate(
        destination_id=7,
        recommended_visit_minutes=120,
        minimum_visit_minutes=90,
        maximum_visit_minutes=180,
    )

    profile = service.create_profile(payload)

    assert profile.destination_id == 7
    assert profile.recommended_visit_minutes == 120
    assert profile.minimum_visit_minutes == 90
    assert profile.maximum_visit_minutes == 180

    repository.create_profile.assert_called_once_with(profile)
    repository.flush.assert_called_once()
    session.commit.assert_called_once()
    repository.refresh.assert_called_once_with(profile)


def test_create_profile_requires_existing_destination():
    service, session, repository = build_service()

    repository.destination_exists.return_value = False

    payload = DestinationPlannerProfileCreate(
        destination_id=99,
    )

    with pytest.raises(DestinationNotFoundError):
        service.create_profile(payload)

    session.rollback.assert_called_once()


def test_create_profile_rejects_duplicate():
    service, session, repository = build_service()

    repository.destination_exists.return_value = True
    repository.profile_exists_for_destination.return_value = True

    payload = DestinationPlannerProfileCreate(
        destination_id=7,
    )

    with pytest.raises(
        DestinationPlannerProfileConflictError
    ):
        service.create_profile(payload)

    session.rollback.assert_called_once()


def test_create_profile_domain_rejects_invalid_duration_range():
    service, _, _ = build_service()

    # Bypass Pydantic intentionally to verify domain defense
    # remains present in the service layer.
    payload = DestinationPlannerProfileCreate.model_construct(
        destination_id=7,
        recommended_visit_minutes=60,
        minimum_visit_minutes=90,
        maximum_visit_minutes=None,
        opening_hours={},
        opening_hours_timezone="Africa/Tripoli",
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    with pytest.raises(
        DestinationPlannerProfileValidationError
    ):
        service.create_profile(payload)


def test_create_profile_domain_rejects_invalid_score():
    service, _, _ = build_service()

    payload = DestinationPlannerProfileCreate.model_construct(
        destination_id=7,
        recommended_visit_minutes=None,
        minimum_visit_minutes=None,
        maximum_visit_minutes=None,
        opening_hours={},
        opening_hours_timezone="Africa/Tripoli",
        planner_priority=101,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    with pytest.raises(
        DestinationPlannerProfileValidationError
    ):
        service.create_profile(payload)


def test_create_verified_profile_sets_verified_at():
    service, _, repository = build_service()

    repository.destination_exists.return_value = True
    repository.profile_exists_for_destination.return_value = False

    payload = DestinationPlannerProfileCreate(
        destination_id=7,
        verification_status=(
            PlannerVerificationStatus.VERIFIED
        ),
    )

    profile = service.create_profile(payload)

    assert profile.verified_at is not None
    assert profile.verified_at.tzinfo is not None


def test_get_profile_returns_profile():
    service, _, repository = build_service()

    profile = DestinationPlannerProfile(
        destination_id=7,
    )

    repository.get_by_destination_id.return_value = profile

    assert service.get_profile(7) is profile


def test_get_profile_raises_when_missing():
    service, _, repository = build_service()

    repository.get_by_destination_id.return_value = None

    with pytest.raises(
        DestinationPlannerProfileNotFoundError
    ):
        service.get_profile(7)


def test_get_profile_database_error_maps_to_persistence_error():
    service, session, repository = build_service()

    repository.get_by_destination_id.side_effect = (
        SQLAlchemyError("database unavailable")
    )
    session.is_active = False

    with pytest.raises(
        DestinationPlannerProfilePersistenceError
    ):
        service.get_profile(7)

    session.rollback.assert_called_once()


def test_update_profile_success():
    service, session, repository = build_service()

    profile = DestinationPlannerProfile(
        destination_id=7,
        recommended_visit_minutes=120,
        minimum_visit_minutes=90,
        maximum_visit_minutes=180,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    repository.get_by_destination_id.return_value = profile

    payload = DestinationPlannerProfileUpdate(
        recommended_visit_minutes=150,
        planner_priority=80,
    )

    result = service.update_profile(
        destination_id=7,
        payload=payload,
    )

    assert result.recommended_visit_minutes == 150
    assert result.planner_priority == 80

    repository.flush.assert_called_once()
    session.commit.assert_called_once()
    repository.refresh.assert_called_once_with(profile)


def test_update_profile_to_verified_sets_timestamp():
    service, _, repository = build_service()

    profile = DestinationPlannerProfile(
        destination_id=7,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    repository.get_by_destination_id.return_value = profile

    payload = DestinationPlannerProfileUpdate(
        verification_status=(
            PlannerVerificationStatus.VERIFIED
        ),
    )

    service.update_profile(
        destination_id=7,
        payload=payload,
    )

    assert profile.verified_at is not None


def test_update_verified_profile_preserves_original_verified_at():
    service, _, repository = build_service()

    original_verified_at = datetime(
        2026,
        8,
        26,
        10,
        0,
        tzinfo=UTC,
    )

    profile = DestinationPlannerProfile(
        destination_id=7,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.VERIFIED
        ),
        verified_at=original_verified_at,
    )

    repository.get_by_destination_id.return_value = profile

    payload = DestinationPlannerProfileUpdate(
        verification_status=(
            PlannerVerificationStatus.VERIFIED
        ),
        planner_priority=80,
    )

    service.update_profile(
        destination_id=7,
        payload=payload,
    )

    assert profile.verified_at == original_verified_at
    assert profile.planner_priority == 80


def test_update_verified_profile_to_reviewed_clears_verified_at():
    service, _, repository = build_service()

    profile = DestinationPlannerProfile(
        destination_id=7,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.VERIFIED
        ),
        verified_at=datetime(
            2026,
            8,
            26,
            10,
            0,
            tzinfo=UTC,
        ),
    )

    repository.get_by_destination_id.return_value = profile

    payload = DestinationPlannerProfileUpdate(
        verification_status=(
            PlannerVerificationStatus.REVIEWED
        ),
    )

    service.update_profile(
        destination_id=7,
        payload=payload,
    )

    assert profile.verified_at is None


def test_update_profile_allows_clearing_duration():
    service, _, repository = build_service()

    profile = DestinationPlannerProfile(
        destination_id=7,
        recommended_visit_minutes=120,
        minimum_visit_minutes=90,
        maximum_visit_minutes=180,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    repository.get_by_destination_id.return_value = profile

    payload = DestinationPlannerProfileUpdate(
        recommended_visit_minutes=None,
    )

    result = service.update_profile(
        destination_id=7,
        payload=payload,
    )

    assert result.recommended_visit_minutes is None


def test_update_profile_validates_merged_duration_state():
    service, session, repository = build_service()

    profile = DestinationPlannerProfile(
        destination_id=7,
        recommended_visit_minutes=120,
        minimum_visit_minutes=90,
        maximum_visit_minutes=180,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    repository.get_by_destination_id.return_value = profile

    payload = DestinationPlannerProfileUpdate(
        minimum_visit_minutes=150,
    )

    with pytest.raises(
        DestinationPlannerProfileValidationError
    ):
        service.update_profile(
            destination_id=7,
            payload=payload,
        )

    session.rollback.assert_called_once()


def test_update_missing_profile_rolls_back():
    service, session, repository = build_service()

    repository.get_by_destination_id.return_value = None

    payload = DestinationPlannerProfileUpdate(
        planner_priority=70,
    )

    with pytest.raises(
        DestinationPlannerProfileNotFoundError
    ):
        service.update_profile(
            destination_id=7,
            payload=payload,
        )

    session.rollback.assert_called_once()


def test_create_integrity_error_rolls_back():
    service, session, repository = build_service()

    repository.destination_exists.return_value = True
    repository.profile_exists_for_destination.return_value = False

    repository.flush.side_effect = IntegrityError(
        "statement",
        {},
        Exception("duplicate"),
    )

    payload = DestinationPlannerProfileCreate(
        destination_id=7,
    )

    with pytest.raises(
        DestinationPlannerProfileIntegrityError
    ):
        service.create_profile(payload)

    session.rollback.assert_called_once()


def test_create_sqlalchemy_error_rolls_back():
    service, session, repository = build_service()

    repository.destination_exists.side_effect = (
        SQLAlchemyError("database unavailable")
    )

    payload = DestinationPlannerProfileCreate(
        destination_id=7,
    )

    with pytest.raises(
        DestinationPlannerProfilePersistenceError
    ):
        service.create_profile(payload)

    session.rollback.assert_called_once()


def test_update_integrity_error_rolls_back():
    service, session, repository = build_service()

    profile = DestinationPlannerProfile(
        destination_id=7,
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    repository.get_by_destination_id.return_value = profile
    repository.flush.side_effect = IntegrityError(
        "statement",
        {},
        Exception("constraint"),
    )

    payload = DestinationPlannerProfileUpdate(
        planner_priority=70,
    )

    with pytest.raises(
        DestinationPlannerProfileIntegrityError
    ):
        service.update_profile(
            destination_id=7,
            payload=payload,
        )

    session.rollback.assert_called_once()


def test_update_sqlalchemy_error_rolls_back():
    service, session, repository = build_service()

    repository.get_by_destination_id.side_effect = (
        SQLAlchemyError("database unavailable")
    )

    payload = DestinationPlannerProfileUpdate(
        planner_priority=70,
    )

    with pytest.raises(
        DestinationPlannerProfilePersistenceError
    ):
        service.update_profile(
            destination_id=7,
            payload=payload,
        )

    session.rollback.assert_called_once()


def test_create_profile_domain_rejects_non_positive_destination_id():
    service, _, _ = build_service()

    payload = DestinationPlannerProfileCreate.model_construct(
        destination_id=0,
        recommended_visit_minutes=None,
        minimum_visit_minutes=None,
        maximum_visit_minutes=None,
        opening_hours={},
        opening_hours_timezone="Africa/Tripoli",
        planner_priority=50,
        meal_suitability=0,
        rest_suitability=0,
        verification_status=(
            PlannerVerificationStatus.UNVERIFIED
        ),
    )

    with pytest.raises(
        DestinationPlannerProfileValidationError
    ):
        service.create_profile(payload)
