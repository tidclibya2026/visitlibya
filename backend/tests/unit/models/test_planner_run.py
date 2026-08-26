from app.models.planner_run import (
    PlannerRun,
    PlannerRunStatus,
)


def test_planner_run_defaults():
    run = PlannerRun(
        user_id=1,
        input_snapshot={},
        itinerary_snapshot={},
        feasibility_snapshot={},
        recommendations_snapshot={},
        optimization_snapshot={},
    )

    assert run.user_id == 1
    assert run.trip_id is None


def test_planner_run_accepts_authoritative_snapshots():
    run = PlannerRun(
        user_id=1,
        trip_id=10,
        feasibility_score=86,
        input_snapshot={
            "days": 3,
            "pace": "balanced",
        },
        itinerary_snapshot={
            "days": [],
        },
        feasibility_snapshot={
            "score": 86,
            "rating": "good",
        },
        recommendations_snapshot={
            "recommendations": [],
        },
        optimization_snapshot={
            "safeToApply": True,
        },
    )

    assert run.feasibility_score == 86
    assert run.input_snapshot["pace"] == "balanced"
    assert run.optimization_snapshot["safeToApply"] is True


def test_planner_run_status_enum_values():
    assert PlannerRunStatus.GENERATED.value == "generated"
    assert PlannerRunStatus.ACCEPTED.value == "accepted"
    assert PlannerRunStatus.REJECTED.value == "rejected"
    assert PlannerRunStatus.SUPERSEDED.value == "superseded"
