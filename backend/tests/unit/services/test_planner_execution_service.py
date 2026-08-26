from datetime import UTC, datetime
from unittest.mock import MagicMock, call

import pytest

from app.core.exceptions import (
    DestinationNotFoundError,
    DestinationUnavailableForTripError,
    PlannerExecutionError,
    TripNotFoundError,
)
from app.models.destination import DestinationStatus
from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.schemas.planner_destination import (
    PlannerDestinationAuthority,
    PlannerDestinationOperationalData,
    PlannerDestinationTranslation,
)
from app.schemas.planner_run import PlannerExecutionRequest
from app.services.planner_execution import (
    ENGINE_VERSION,
    PLANNER_VERSION,
    PlannerExecutionService,
)


def authority(
    destination_id: int = 1,
    slug: str = "tripoli",
    profile_state: str = "verified",
    *,
    published: bool = True,
) -> PlannerDestinationAuthority:
    return PlannerDestinationAuthority(
        destination_id=destination_id,
        slug=slug,
        category_code="historic-cities",
        latitude=32.8872,
        longitude=13.1913,
        municipality="Tripoli",
        region="Tripoli",
        editorial_priority_order=1,
        publication_status=(DestinationStatus.PUBLISHED if published else DestinationStatus.DRAFT),
        is_active=True,
        translations=[PlannerDestinationTranslation(
            language_code="en", name="Tripoli", short_description="Historic capital",
            visitor_information=None, accessibility_information=None,
        )],
        profile_state=profile_state,
        profile_verification_status=None if profile_state == "missing" else profile_state,
        profile_verified_at=datetime(2026, 1, 1, tzinfo=UTC) if profile_state == "verified" else None,
        operational_data=PlannerDestinationOperationalData(
            recommended_visit_minutes=120, minimum_visit_minutes=None,
            maximum_visit_minutes=None, opening_hours=None,
            opening_hours_timezone=None, access_status=None, road_access=None,
            road_surface=None, road_condition=None, planner_priority=80,
            meal_suitability=50, rest_suitability=50, data_source="governed",
        ),
    )


def request(**overrides) -> PlannerExecutionRequest:
    values = {
        "destination_ids": [1], "days": 1, "pace": "balanced",
        "starting_point": "tripoli", "interests": ["history"],
        "traveler_type": "solo",
    }
    values.update(overrides)
    return PlannerExecutionRequest(**values)


def make_service(*, resolved=None, executor=None):
    authority_service = MagicMock()
    authority_service.get_authority.return_value = resolved or authority()
    authority_service.get_authority_by_slug.return_value = resolved or authority()
    run_service = MagicMock()
    run_service.create_run.side_effect = lambda **values: PlannerRun(
        id=9, created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        status=PlannerRunStatus.GENERATED, **values,
    )
    audit = MagicMock()
    kwargs = {"audit_logger": audit}
    if executor is not None:
        kwargs["executor"] = executor
    return PlannerExecutionService(authority_service, run_service, **kwargs), authority_service, run_service, audit


def test_owned_trip_execution_resolves_authority_and_persists_generated_run():
    service, authority_service, run_service, audit = make_service()
    run, result, authorities = service.execute(
        actor_id=7, trip_id=22, payload=request(), request_id="request-1",
    )
    run_service.require_owned_trip.assert_called_once_with(trip_id=22, user_id=7)
    authority_service.get_authority.assert_called_once_with(1)
    assert authorities[0].destination_id == 1
    assert run.status == PlannerRunStatus.GENERATED
    assert result["selectedCount"] == 1
    persisted = run_service.create_run.call_args.kwargs
    assert persisted["planner_version"] == PLANNER_VERSION
    assert persisted["engine_version"] == ENGINE_VERSION
    assert persisted["input_snapshot"]["destination_authority"][0]["destination_id"] == 1
    assert persisted["itinerary_snapshot"]["days"] == result["days"]
    assert persisted["feasibility_snapshot"] == result["feasibility"]
    assert persisted["recommendations_snapshot"] == result["recommendations"]
    assert persisted["optimization_snapshot"] == result["optimization"]
    audit.assert_called_once_with(
        "planner_run_executed", actor_id=7, request_id="request-1",
        planner_run_id=9, trip_id=22, status="generated",
    )


def test_ownership_failure_happens_before_destination_resolution():
    service, authority_service, run_service, _ = make_service()
    run_service.require_owned_trip.side_effect = TripNotFoundError()
    with pytest.raises(TripNotFoundError):
        service.execute(actor_id=8, trip_id=22, payload=request())
    authority_service.get_authority.assert_not_called()
    run_service.create_run.assert_not_called()


def test_ids_and_slugs_are_resolved_only_through_authority_service():
    first, second = authority(1, "tripoli"), authority(2, "benghazi")
    service, authority_service, _, _ = make_service()
    authority_service.get_authority.return_value = first
    authority_service.get_authority_by_slug.return_value = second
    service.execute(
        actor_id=7, trip_id=22,
        payload=request(destination_ids=[1], destination_slugs=["BENGHAZI"]),
    )
    assert authority_service.method_calls[:2] == [
        call.get_authority(1), call.get_authority_by_slug("benghazi"),
    ]


def test_unverified_authority_remains_unverified_in_input_and_result():
    service, _, run_service, _ = make_service(resolved=authority(profile_state="unverified"))
    _, result, authorities = service.execute(actor_id=7, trip_id=22, payload=request())
    assert authorities[0].profile_state == "unverified"
    assert result["days"][0]["destinations"][0]["planner_authority"]["profileState"] == "unverified"
    snapshot = run_service.create_run.call_args.kwargs["input_snapshot"]
    assert snapshot["destination_authority"][0]["profile_state"] == "unverified"
    assert snapshot["destination_authority"][0]["profile_verified_at"] is None


def test_unknown_destination_is_rejected_without_persisting():
    service, authority_service, run_service, audit = make_service()
    authority_service.get_authority.side_effect = DestinationNotFoundError()
    with pytest.raises(DestinationNotFoundError):
        service.execute(actor_id=7, trip_id=22, payload=request())
    run_service.create_run.assert_not_called()
    audit.assert_not_called()


def test_unpublished_destination_is_rejected_without_weakening_governance():
    service, _, run_service, _ = make_service(resolved=authority(published=False))
    with pytest.raises(DestinationUnavailableForTripError):
        service.execute(actor_id=7, trip_id=22, payload=request())
    run_service.create_run.assert_not_called()


def test_planner_failure_is_safe_and_not_persisted():
    service, _, run_service, audit = make_service(executor=MagicMock(side_effect=RuntimeError("secret")))
    with pytest.raises(PlannerExecutionError, match="Planner execution failed"):
        service.execute(actor_id=7, trip_id=22, payload=request())
    run_service.create_run.assert_not_called()
    audit.assert_not_called()


def test_repeated_execution_is_deterministic_for_same_authority_and_preferences():
    service, _, run_service, _ = make_service()
    first = service.execute(actor_id=7, trip_id=22, payload=request())[1]
    second = service.execute(actor_id=7, trip_id=22, payload=request())[1]
    assert first == second
    assert run_service.create_run.call_count == 2
