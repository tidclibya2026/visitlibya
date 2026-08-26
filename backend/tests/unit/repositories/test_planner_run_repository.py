from unittest.mock import MagicMock

from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.repositories.planner_run import PlannerRunRepository


def make_run(**overrides):
    values = {
        "user_id": 1,
        "input_snapshot": {},
        "itinerary_snapshot": {},
        "feasibility_snapshot": {},
        "recommendations_snapshot": {},
        "optimization_snapshot": {},
    }
    values.update(overrides)
    return PlannerRun(**values)


def test_create_planner_run_adds_model():
    session = MagicMock()
    repository = PlannerRunRepository(session)
    planner_run = make_run()

    repository.create_planner_run(planner_run)

    session.add.assert_called_once_with(planner_run)


def test_get_owned_planner_run_by_id_returns_owned_run():
    session = MagicMock()
    repository = PlannerRunRepository(session)
    expected = make_run(id=11, user_id=7)

    session.scalar.return_value = expected

    result = repository.get_owned_planner_run_by_id(
        planner_run_id=11,
        user_id=7,
    )

    assert result is expected
    session.scalar.assert_called_once()


def test_list_user_planner_runs_returns_sequence():
    session = MagicMock()
    repository = PlannerRunRepository(session)

    first = make_run(id=3, user_id=5)
    second = make_run(id=2, user_id=5)

    scalars = MagicMock()
    scalars.all.return_value = [first, second]
    session.scalars.return_value = scalars

    result = repository.list_user_planner_runs(
        user_id=5,
        skip=0,
        limit=20,
    )

    assert result == [first, second]
    session.scalars.assert_called_once()


def test_list_trip_planner_runs_returns_sequence():
    session = MagicMock()
    repository = PlannerRunRepository(session)

    planner_run = make_run(
        id=8,
        trip_id=42,
        user_id=5,
    )

    scalars = MagicMock()
    scalars.all.return_value = [planner_run]
    session.scalars.return_value = scalars

    result = repository.list_trip_planner_runs(
        trip_id=42,
        user_id=5,
    )

    assert result == [planner_run]


def test_get_latest_for_trip_returns_latest_run():
    session = MagicMock()
    repository = PlannerRunRepository(session)

    expected = make_run(
        id=21,
        trip_id=9,
        user_id=4,
    )

    session.scalar.return_value = expected

    result = repository.get_latest_for_trip(
        trip_id=9,
        user_id=4,
    )

    assert result is expected


def test_get_latest_accepted_for_trip_returns_run():
    session = MagicMock()
    repository = PlannerRunRepository(session)

    expected = make_run(
        id=33,
        trip_id=14,
        user_id=6,
        status=PlannerRunStatus.ACCEPTED,
    )

    session.scalar.return_value = expected

    result = repository.get_latest_accepted_for_trip(
        trip_id=14,
        user_id=6,
    )

    assert result is expected


def test_update_status_returns_updated_run():
    session = MagicMock()
    repository = PlannerRunRepository(session)

    expected = make_run(
        id=18,
        user_id=2,
        status=PlannerRunStatus.ACCEPTED,
    )

    session.scalar.return_value = expected

    result = repository.update_status(
        planner_run_id=18,
        user_id=2,
        status=PlannerRunStatus.ACCEPTED,
    )

    assert result is expected


def test_supersede_other_trip_runs_returns_updated_ids():
    session = MagicMock()
    repository = PlannerRunRepository(session)

    scalars = MagicMock()
    scalars.all.return_value = [12, 13]
    session.scalars.return_value = scalars

    result = repository.supersede_other_trip_runs(
        trip_id=4,
        user_id=7,
        accepted_run_id=14,
    )

    assert result == [12, 13]


def test_update_evidence_returns_updated_run():
    session = MagicMock()
    repository = PlannerRunRepository(session)

    expected = make_run(
        id=50,
        user_id=3,
        feasibility_score=91,
        feasibility_snapshot={"score": 91},
        recommendations_snapshot={"items": []},
        optimization_snapshot={"safeToApply": True},
    )

    session.scalar.return_value = expected

    result = repository.update_evidence(
        planner_run_id=50,
        user_id=3,
        feasibility_score=91,
        feasibility_snapshot={"score": 91},
        recommendations_snapshot={"items": []},
        optimization_snapshot={"safeToApply": True},
    )

    assert result is expected
