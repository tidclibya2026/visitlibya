from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.planner_run import PlannerRunStatus
from app.schemas.planner_run import (
    PlannerRunCreate,
    PlannerRunEvidenceUpdate,
    PlannerRunResponse,
    PlannerRunSummaryResponse,
)


def valid_create_payload():
    return {
        "trip_id": 12,
        "planner_version": 1,
        "engine_version": "visitlibya-ai-planner-v1",
        "feasibility_score": 84,
        "input_snapshot": {"pace": "balanced"},
        "itinerary_snapshot": {"days": []},
        "feasibility_snapshot": {"score": 84},
        "recommendations_snapshot": {"items": []},
        "optimization_snapshot": {"safeToApply": True},
    }


def test_planner_run_create_accepts_valid_payload():
    payload = PlannerRunCreate(**valid_create_payload())

    assert payload.trip_id == 12
    assert payload.planner_version == 1
    assert payload.feasibility_score == 84


def test_planner_run_create_allows_standalone_run():
    values = valid_create_payload()
    values["trip_id"] = None

    payload = PlannerRunCreate(**values)

    assert payload.trip_id is None


@pytest.mark.parametrize("trip_id", [0, -1])
def test_planner_run_create_rejects_invalid_trip_id(trip_id):
    values = valid_create_payload()
    values["trip_id"] = trip_id

    with pytest.raises(ValidationError):
        PlannerRunCreate(**values)


@pytest.mark.parametrize("score", [-1, 101])
def test_planner_run_create_rejects_invalid_feasibility_score(score):
    values = valid_create_payload()
    values["feasibility_score"] = score

    with pytest.raises(ValidationError):
        PlannerRunCreate(**values)


def test_planner_run_create_requires_snapshots():
    values = valid_create_payload()
    values.pop("input_snapshot")

    with pytest.raises(ValidationError):
        PlannerRunCreate(**values)


def test_evidence_update_accepts_valid_payload():
    payload = PlannerRunEvidenceUpdate(
        feasibility_score=91,
        feasibility_snapshot={"score": 91},
        recommendations_snapshot={"items": ["reduce travel"]},
        optimization_snapshot={"recommended": True},
    )

    assert payload.feasibility_score == 91


@pytest.mark.parametrize("score", [-1, 101])
def test_evidence_update_rejects_invalid_score(score):
    with pytest.raises(ValidationError):
        PlannerRunEvidenceUpdate(
            feasibility_score=score,
            feasibility_snapshot={},
            recommendations_snapshot={},
            optimization_snapshot={},
        )


def test_planner_run_response_supports_attribute_models():
    now = datetime.now(timezone.utc)

    class Source:
        id = 8
        trip_id = 15
        user_id = 4
        planner_version = 1
        engine_version = "visitlibya-ai-planner-v1"
        status = PlannerRunStatus.ACCEPTED
        feasibility_score = 90
        input_snapshot = {}
        itinerary_snapshot = {}
        feasibility_snapshot = {"score": 90}
        recommendations_snapshot = {}
        optimization_snapshot = {}
        created_at = now
        updated_at = now

    result = PlannerRunResponse.model_validate(Source())

    assert result.id == 8
    assert result.status == PlannerRunStatus.ACCEPTED
    assert result.feasibility_score == 90


def test_planner_run_summary_response_supports_attribute_models():
    now = datetime.now(timezone.utc)

    class Source:
        id = 9
        trip_id = None
        planner_version = 1
        engine_version = "visitlibya-ai-planner-v1"
        status = PlannerRunStatus.GENERATED
        feasibility_score = None
        created_at = now
        updated_at = now

    result = PlannerRunSummaryResponse.model_validate(Source())

    assert result.id == 9
    assert result.trip_id is None
    assert result.status == PlannerRunStatus.GENERATED
