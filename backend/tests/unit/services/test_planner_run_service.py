from unittest.mock import MagicMock

import pytest

from app.core.exceptions import TripNotFoundError
from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.services.planner_run import PlannerRunService


def make_run(**overrides):
    values = {
        "id": 1,
        "user_id": 1,
        "trip_id": 10,
        "status": PlannerRunStatus.GENERATED,
        "input_snapshot": {},
        "itinerary_snapshot": {},
        "feasibility_snapshot": {},
        "recommendations_snapshot": {},
        "optimization_snapshot": {},
    }
    values.update(overrides)
    return PlannerRun(**values)


def test_create_run_adds_generated_run():
    session = MagicMock()
    repository = MagicMock()
    repository.owned_trip_exists.return_value = True
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    result = service.create_run(
        user_id=7,
        trip_id=22,
        feasibility_score=84,
        input_snapshot={"pace": "balanced"},
        itinerary_snapshot={"days": []},
        feasibility_snapshot={"score": 84},
        recommendations_snapshot={"items": []},
        optimization_snapshot={"safeToApply": True},
    )

    assert result.user_id == 7
    assert result.trip_id == 22
    assert result.status == PlannerRunStatus.GENERATED
    assert result.feasibility_score == 84
    repository.create_planner_run.assert_called_once_with(result)


def test_create_run_rejects_trip_not_owned_by_user():
    session = MagicMock()
    repository = MagicMock()
    repository.owned_trip_exists.return_value = False
    service = PlannerRunService(session=session, repository=repository)

    with pytest.raises(TripNotFoundError):
        service.create_run(
            user_id=7,
            trip_id=22,
            input_snapshot={},
            itinerary_snapshot={},
            feasibility_snapshot={},
            recommendations_snapshot={},
            optimization_snapshot={},
        )
    repository.create_planner_run.assert_not_called()


@pytest.mark.parametrize("score", [-1, 101])
def test_create_run_rejects_invalid_feasibility_score(score):
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    with pytest.raises(ValueError):
        service.create_run(
            user_id=1,
            trip_id=None,
            feasibility_score=score,
            input_snapshot={},
            itinerary_snapshot={},
            feasibility_snapshot={},
            recommendations_snapshot={},
            optimization_snapshot={},
        )

    repository.create_planner_run.assert_not_called()


def test_get_owned_run_delegates_to_repository():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )
    expected = make_run(id=9, user_id=4)
    repository.get_owned_planner_run_by_id.return_value = expected

    result = service.get_owned_run(
        planner_run_id=9,
        user_id=4,
    )

    assert result is expected
    repository.get_owned_planner_run_by_id.assert_called_once_with(
        planner_run_id=9,
        user_id=4,
    )


def test_accept_run_returns_none_when_not_owned():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )
    repository.get_owned_planner_run_by_id.return_value = None

    result = service.accept_run(
        planner_run_id=50,
        user_id=3,
    )

    assert result is None
    repository.update_status.assert_not_called()


def test_accept_run_accepts_generated_run_and_supersedes_others():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    existing = make_run(
        id=14,
        user_id=7,
        trip_id=44,
        status=PlannerRunStatus.GENERATED,
    )
    accepted = make_run(
        id=14,
        user_id=7,
        trip_id=44,
        status=PlannerRunStatus.ACCEPTED,
    )

    repository.get_owned_planner_run_by_id.return_value = existing
    repository.update_status.return_value = accepted

    result = service.accept_run(
        planner_run_id=14,
        user_id=7,
    )

    assert result is accepted

    repository.update_status.assert_called_once_with(
        planner_run_id=14,
        user_id=7,
        status=PlannerRunStatus.ACCEPTED,
    )

    repository.supersede_other_trip_runs.assert_called_once_with(
        trip_id=44,
        user_id=7,
        accepted_run_id=14,
    )


def test_accept_run_is_idempotent_for_already_accepted_run():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )
    accepted = make_run(status=PlannerRunStatus.ACCEPTED)
    repository.get_owned_planner_run_by_id.return_value = accepted

    result = service.accept_run(
        planner_run_id=1,
        user_id=1,
    )

    assert result is accepted
    repository.update_status.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        PlannerRunStatus.REJECTED,
        PlannerRunStatus.SUPERSEDED,
    ],
)
def test_accept_run_rejects_invalid_previous_status(status):
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    repository.get_owned_planner_run_by_id.return_value = make_run(
        status=status,
    )

    with pytest.raises(ValueError):
        service.accept_run(
            planner_run_id=1,
            user_id=1,
        )


def test_reject_run_rejects_generated_run():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    repository.get_owned_planner_run_by_id.return_value = make_run(
        id=3,
        status=PlannerRunStatus.GENERATED,
    )

    rejected = make_run(
        id=3,
        status=PlannerRunStatus.REJECTED,
    )
    repository.update_status.return_value = rejected

    result = service.reject_run(
        planner_run_id=3,
        user_id=1,
    )

    assert result is rejected


def test_reject_run_refuses_accepted_run():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    repository.get_owned_planner_run_by_id.return_value = make_run(
        status=PlannerRunStatus.ACCEPTED,
    )

    with pytest.raises(ValueError):
        service.reject_run(
            planner_run_id=1,
            user_id=1,
        )


def test_update_evidence_updates_generated_run():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    repository.get_owned_planner_run_by_id.return_value = make_run(
        id=20,
        status=PlannerRunStatus.GENERATED,
    )

    updated = make_run(
        id=20,
        feasibility_score=92,
    )
    repository.update_evidence.return_value = updated

    result = service.update_evidence(
        planner_run_id=20,
        user_id=1,
        feasibility_score=92,
        feasibility_snapshot={"score": 92},
        recommendations_snapshot={"items": []},
        optimization_snapshot={"safeToApply": True},
    )

    assert result is updated


@pytest.mark.parametrize("score", [-1, 101])
def test_update_evidence_rejects_invalid_score(score):
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    with pytest.raises(ValueError):
        service.update_evidence(
            planner_run_id=1,
            user_id=1,
            feasibility_score=score,
            feasibility_snapshot={},
            recommendations_snapshot={},
            optimization_snapshot={},
        )


@pytest.mark.parametrize(
    "status",
    [
        PlannerRunStatus.ACCEPTED,
        PlannerRunStatus.REJECTED,
        PlannerRunStatus.SUPERSEDED,
    ],
)
def test_update_evidence_rejects_terminal_runs(status):
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    repository.get_owned_planner_run_by_id.return_value = make_run(
        status=status,
    )

    with pytest.raises(ValueError):
        service.update_evidence(
            planner_run_id=1,
            user_id=1,
            feasibility_score=75,
            feasibility_snapshot={"score": 75},
            recommendations_snapshot={},
            optimization_snapshot={},
        )

def test_create_run_flushes_and_commits_transaction():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    service.create_run(
        user_id=1,
        trip_id=None,
        input_snapshot={},
        itinerary_snapshot={},
        feasibility_snapshot={},
        recommendations_snapshot={},
        optimization_snapshot={},
    )

    repository.flush.assert_called_once()
    session.commit.assert_called_once()


def test_accept_run_flushes_and_commits_transaction():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    existing = make_run(
        id=14,
        user_id=7,
        trip_id=44,
        status=PlannerRunStatus.GENERATED,
    )
    accepted = make_run(
        id=14,
        user_id=7,
        trip_id=44,
        status=PlannerRunStatus.ACCEPTED,
    )

    repository.get_owned_planner_run_by_id.return_value = existing
    repository.update_status.return_value = accepted

    result = service.accept_run(
        planner_run_id=14,
        user_id=7,
    )

    assert result is accepted
    repository.flush.assert_called_once()
    session.commit.assert_called_once()

def test_create_run_flushes_and_commits_transaction():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    service.create_run(
        user_id=1,
        trip_id=None,
        input_snapshot={},
        itinerary_snapshot={},
        feasibility_snapshot={},
        recommendations_snapshot={},
        optimization_snapshot={},
    )

    repository.flush.assert_called_once()
    session.commit.assert_called_once()


def test_accept_run_flushes_and_commits_transaction():
    session = MagicMock()
    repository = MagicMock()
    service = PlannerRunService(
        session=session,
        repository=repository,
    )

    existing = make_run(
        id=14,
        user_id=7,
        trip_id=44,
        status=PlannerRunStatus.GENERATED,
    )
    accepted = make_run(
        id=14,
        user_id=7,
        trip_id=44,
        status=PlannerRunStatus.ACCEPTED,
    )

    repository.get_owned_planner_run_by_id.return_value = existing
    repository.update_status.return_value = accepted

    result = service.accept_run(
        planner_run_id=14,
        user_id=7,
    )

    assert result is accepted
    repository.flush.assert_called_once()
    session.commit.assert_called_once()
