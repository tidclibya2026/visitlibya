from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DestinationNotFoundError, DestinationPersistenceError
from app.models.category import Category
from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.models.destination_planner_profile import (
    DestinationPlannerProfile,
    PlannerAccessStatus,
    PlannerRoadAccess,
    PlannerRoadCondition,
    PlannerRoadSurface,
    PlannerVerificationStatus,
)
from app.services.planner_destination import PlannerDestinationAuthorityService


def make_destination(profile: DestinationPlannerProfile | None) -> Destination:
    destination = Destination(
        id=7,
        slug="leptis-magna",
        category_id=2,
        status=DestinationStatus.DRAFT,
        latitude=32.6389,
        longitude=14.2906,
        municipality="Khoms",
        region="Tripolitania",
        priority_order=4,
        is_active=True,
    )
    destination.category = Category(id=2, code="archaeology", name_ar="آثار", name_en="Archaeology")
    destination.translations = [
        DestinationTranslation(
            language_code="en", name="Leptis Magna", short_description="Ancient city"
        ),
        DestinationTranslation(language_code="ar", name="لبدة الكبرى"),
    ]
    destination.planner_profile = profile
    return destination


def make_profile(**overrides) -> DestinationPlannerProfile:
    values = {
        "destination_id": 7,
        "recommended_visit_minutes": 180,
        "minimum_visit_minutes": 120,
        "maximum_visit_minutes": 240,
        "opening_hours": {"z": {"close": "17:00", "open": "09:00"}, "a": []},
        "opening_hours_timezone": "Africa/Tripoli",
        "access_status": PlannerAccessStatus.OPEN,
        "road_access": PlannerRoadAccess.STANDARD,
        "road_surface": PlannerRoadSurface.PAVED,
        "road_condition": PlannerRoadCondition.GOOD,
        "planner_priority": 82,
        "meal_suitability": 20,
        "rest_suitability": 30,
        "data_source": "institutional review",
        "verification_status": PlannerVerificationStatus.UNVERIFIED,
    }
    values.update(overrides)
    return DestinationPlannerProfile(**values)


def test_missing_profile_is_explicit_and_never_guesses_values() -> None:
    result = PlannerDestinationAuthorityService.assemble(make_destination(None))
    assert result.profile_state == "missing"
    assert result.profile_verification_status is None
    assert all(value is None for value in result.operational_data.model_dump().values())
    assert result.latitude == 32.6389 and result.longitude == 14.2906
    assert result.publication_status == DestinationStatus.DRAFT


def test_unverified_profile_preserves_metadata_and_separate_priorities() -> None:
    result = PlannerDestinationAuthorityService.assemble(make_destination(make_profile()))
    assert result.profile_state == "unverified"
    assert result.profile_verification_status == PlannerVerificationStatus.UNVERIFIED
    assert result.editorial_priority_order == 4
    assert result.operational_data.planner_priority == 82
    assert list(result.operational_data.opening_hours or {}) == ["a", "z"]
    assert [item.language_code for item in result.translations] == ["ar", "en"]


def test_verified_profile_preserves_verification_timestamp() -> None:
    verified_at = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    result = PlannerDestinationAuthorityService.assemble(
        make_destination(
            make_profile(
                verification_status=PlannerVerificationStatus.VERIFIED,
                verified_at=verified_at,
            )
        )
    )
    assert result.profile_state == "verified"
    assert result.profile_verified_at == verified_at


def test_get_authority_maps_missing_and_database_failures() -> None:
    session = MagicMock()
    repository = MagicMock()
    service = PlannerDestinationAuthorityService(session, repository)
    repository.get_planner_authority_by_id.return_value = None
    with pytest.raises(DestinationNotFoundError):
        service.get_authority(7)

    repository.get_planner_authority_by_id.side_effect = SQLAlchemyError("private")
    session.is_active = False
    with pytest.raises(DestinationPersistenceError):
        service.get_authority(7)
    session.rollback.assert_called_once()


def test_get_authority_rejects_invalid_id() -> None:
    with pytest.raises(ValueError):
        PlannerDestinationAuthorityService(MagicMock()).get_authority(0)
