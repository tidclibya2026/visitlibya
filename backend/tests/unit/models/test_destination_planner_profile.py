from app.models.destination_planner_profile import (
    DestinationPlannerProfile,
    PlannerAccessStatus,
    PlannerRoadAccess,
    PlannerRoadCondition,
    PlannerRoadSurface,
    PlannerVerificationStatus,
)


def test_destination_planner_profile_defaults():
    profile = DestinationPlannerProfile(
        destination_id=1,
    )

    assert profile.destination_id == 1
    assert profile.recommended_visit_minutes is None
    assert profile.minimum_visit_minutes is None
    assert profile.maximum_visit_minutes is None

    assert profile.opening_hours is None or profile.opening_hours == {}

    assert profile.access_status in (
        None,
        PlannerAccessStatus.UNKNOWN,
    )
    assert profile.road_access in (
        None,
        PlannerRoadAccess.UNKNOWN,
    )
    assert profile.road_surface in (
        None,
        PlannerRoadSurface.UNKNOWN,
    )
    assert profile.road_condition in (
        None,
        PlannerRoadCondition.UNKNOWN,
    )
    assert profile.verification_status in (
        None,
        PlannerVerificationStatus.UNVERIFIED,
    )


def test_destination_planner_profile_accepts_planner_values():
    profile = DestinationPlannerProfile(
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
        meal_suitability=20,
        rest_suitability=35,
        data_source="institutional-review",
        verification_status=PlannerVerificationStatus.VERIFIED,
    )

    assert profile.destination_id == 7
    assert profile.recommended_visit_minutes == 120
    assert profile.minimum_visit_minutes == 90
    assert profile.maximum_visit_minutes == 180

    assert profile.opening_hours["monday"]["open"] == "09:00"

    assert profile.access_status == PlannerAccessStatus.OPEN
    assert profile.road_access == PlannerRoadAccess.FOUR_WHEEL_DRIVE
    assert profile.road_surface == PlannerRoadSurface.OFF_ROAD
    assert profile.road_condition == PlannerRoadCondition.DIFFICULT

    assert profile.planner_priority == 90
    assert profile.meal_suitability == 20
    assert profile.rest_suitability == 35

    assert profile.data_source == "institutional-review"
    assert (
        profile.verification_status
        == PlannerVerificationStatus.VERIFIED
    )


def test_destination_planner_profile_enum_values_are_stable():
    assert PlannerAccessStatus.UNKNOWN.value == "unknown"
    assert PlannerAccessStatus.OPEN.value == "open"
    assert PlannerAccessStatus.RESTRICTED.value == "restricted"
    assert PlannerAccessStatus.SEASONAL.value == "seasonal"
    assert PlannerAccessStatus.CLOSED.value == "closed"

    assert PlannerRoadAccess.STANDARD.value == "standard"
    assert PlannerRoadAccess.FOUR_WHEEL_DRIVE.value == "four_wheel_drive"
    assert PlannerRoadAccess.GUIDED_ONLY.value == "guided_only"

    assert PlannerRoadSurface.PAVED.value == "paved"
    assert PlannerRoadSurface.MIXED.value == "mixed"
    assert PlannerRoadSurface.UNPAVED.value == "unpaved"
    assert PlannerRoadSurface.OFF_ROAD.value == "off_road"

    assert PlannerRoadCondition.GOOD.value == "good"
    assert PlannerRoadCondition.MODERATE.value == "moderate"
    assert PlannerRoadCondition.DIFFICULT.value == "difficult"
    assert (
        PlannerRoadCondition.VERY_DIFFICULT.value
        == "very_difficult"
    )

    assert (
        PlannerVerificationStatus.UNVERIFIED.value
        == "unverified"
    )
    assert PlannerVerificationStatus.REVIEWED.value == "reviewed"
    assert PlannerVerificationStatus.VERIFIED.value == "verified"
