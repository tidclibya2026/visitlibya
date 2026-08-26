from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.destination_planner_profile import (
    PlannerAccessStatus,
    PlannerRoadAccess,
    PlannerRoadCondition,
    PlannerRoadSurface,
    PlannerVerificationStatus,
)
from app.schemas.destination_planner_profile import (
    DestinationPlannerProfileCreate,
    DestinationPlannerProfileRead,
    DestinationPlannerProfileUpdate,
)


def test_create_profile_defaults():
    payload = DestinationPlannerProfileCreate(
        destination_id=7,
    )

    assert payload.destination_id == 7
    assert payload.opening_hours == {}
    assert payload.opening_hours_timezone == "Africa/Tripoli"

    assert payload.access_status == PlannerAccessStatus.UNKNOWN
    assert payload.road_access == PlannerRoadAccess.UNKNOWN
    assert payload.road_surface == PlannerRoadSurface.UNKNOWN
    assert payload.road_condition == PlannerRoadCondition.UNKNOWN

    assert payload.planner_priority == 50
    assert payload.meal_suitability == 0
    assert payload.rest_suitability == 0

    assert (
        payload.verification_status
        == PlannerVerificationStatus.UNVERIFIED
    )


def test_create_profile_accepts_authoritative_values():
    payload = DestinationPlannerProfileCreate(
        destination_id=7,
        recommended_visit_minutes=120,
        minimum_visit_minutes=90,
        maximum_visit_minutes=180,
        opening_hours={
            "monday": {
                "open": "09:00",
                "close": "17:00",
            }
        },
        access_status=PlannerAccessStatus.OPEN,
        road_access=PlannerRoadAccess.FOUR_WHEEL_DRIVE,
        road_surface=PlannerRoadSurface.OFF_ROAD,
        road_condition=PlannerRoadCondition.DIFFICULT,
        planner_priority=90,
        meal_suitability=25,
        rest_suitability=40,
        data_source="institutional-review",
        verification_status=PlannerVerificationStatus.REVIEWED,
    )

    assert payload.recommended_visit_minutes == 120
    assert payload.minimum_visit_minutes == 90
    assert payload.maximum_visit_minutes == 180
    assert payload.planner_priority == 90


@pytest.mark.parametrize(
    "field,value",
    [
        ("planner_priority", -1),
        ("planner_priority", 101),
        ("meal_suitability", -1),
        ("meal_suitability", 101),
        ("rest_suitability", -1),
        ("rest_suitability", 101),
    ],
)
def test_create_rejects_out_of_range_scores(
    field,
    value,
):
    with pytest.raises(ValidationError):
        DestinationPlannerProfileCreate(
            destination_id=7,
            **{field: value},
        )


@pytest.mark.parametrize(
    "field",
    [
        "recommended_visit_minutes",
        "minimum_visit_minutes",
        "maximum_visit_minutes",
    ],
)
def test_create_rejects_non_positive_duration(field):
    with pytest.raises(ValidationError):
        DestinationPlannerProfileCreate(
            destination_id=7,
            **{field: 0},
        )


def test_create_rejects_minimum_above_recommended():
    with pytest.raises(
        ValidationError,
        match="minimum_visit_minutes cannot exceed",
    ):
        DestinationPlannerProfileCreate(
            destination_id=7,
            minimum_visit_minutes=120,
            recommended_visit_minutes=90,
        )


def test_create_rejects_maximum_below_recommended():
    with pytest.raises(
        ValidationError,
        match="maximum_visit_minutes cannot be below",
    ):
        DestinationPlannerProfileCreate(
            destination_id=7,
            recommended_visit_minutes=120,
            maximum_visit_minutes=90,
        )


def test_create_rejects_minimum_above_maximum():
    with pytest.raises(
        ValidationError,
        match="minimum_visit_minutes cannot exceed",
    ):
        DestinationPlannerProfileCreate(
            destination_id=7,
            minimum_visit_minutes=180,
            maximum_visit_minutes=120,
        )


def test_create_rejects_invalid_destination_id():
    with pytest.raises(ValidationError):
        DestinationPlannerProfileCreate(
            destination_id=0,
        )


def test_create_rejects_empty_timezone():
    with pytest.raises(ValidationError):
        DestinationPlannerProfileCreate(
            destination_id=7,
            opening_hours_timezone="",
        )


def test_update_allows_partial_payload():
    payload = DestinationPlannerProfileUpdate(
        planner_priority=75,
    )

    values = payload.model_dump(exclude_unset=True)

    assert values == {
        "planner_priority": 75,
    }


def test_update_accepts_null_duration():
    payload = DestinationPlannerProfileUpdate(
        recommended_visit_minutes=None,
    )

    values = payload.model_dump(exclude_unset=True)

    assert "recommended_visit_minutes" in values
    assert values["recommended_visit_minutes"] is None


def test_update_rejects_invalid_score():
    with pytest.raises(ValidationError):
        DestinationPlannerProfileUpdate(
            planner_priority=101,
        )


def test_read_schema_supports_attributes():
    class Record:
        id = 12
        destination_id = 7

        recommended_visit_minutes = 120
        minimum_visit_minutes = 90
        maximum_visit_minutes = 180

        opening_hours = {}
        opening_hours_timezone = "Africa/Tripoli"

        access_status = PlannerAccessStatus.OPEN
        road_access = PlannerRoadAccess.STANDARD
        road_surface = PlannerRoadSurface.PAVED
        road_condition = PlannerRoadCondition.GOOD

        planner_priority = 80
        meal_suitability = 20
        rest_suitability = 30

        data_source = "institutional-review"

        verification_status = (
            PlannerVerificationStatus.VERIFIED
        )

        verified_at = datetime(
            2026,
            8,
            26,
            12,
            0,
            tzinfo=UTC,
        )
        created_at = datetime(
            2026,
            8,
            26,
            10,
            0,
            tzinfo=UTC,
        )
        updated_at = datetime(
            2026,
            8,
            26,
            12,
            0,
            tzinfo=UTC,
        )

    response = DestinationPlannerProfileRead.model_validate(
        Record()
    )

    assert response.id == 12
    assert response.destination_id == 7
    assert response.verification_status == (
        PlannerVerificationStatus.VERIFIED
    )
    assert response.verified_at is not None


def test_create_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        DestinationPlannerProfileCreate(
            destination_id=7,
            latitude=32.9,
        )


def test_update_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        DestinationPlannerProfileUpdate(
            latitude=32.9,
        )
