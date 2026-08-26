from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.repositories.planner_run import PlannerRunRepository


class PlannerRunService:
    def __init__(
        self,
        session: Session,
        repository: PlannerRunRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or PlannerRunRepository(session)

    def create_run(
        self,
        *,
        user_id: int,
        trip_id: int | None,
        input_snapshot: dict,
        itinerary_snapshot: dict,
        feasibility_snapshot: dict,
        recommendations_snapshot: dict,
        optimization_snapshot: dict,
        feasibility_score: int | None = None,
        planner_version: int = 1,
        engine_version: str = "visitlibya-ai-planner-v1",
    ) -> PlannerRun:
        self._validate_feasibility_score(feasibility_score)

        planner_run = PlannerRun(
            user_id=user_id,
            trip_id=trip_id,
            planner_version=planner_version,
            engine_version=engine_version,
            status=PlannerRunStatus.GENERATED,
            feasibility_score=feasibility_score,
            input_snapshot=input_snapshot,
            itinerary_snapshot=itinerary_snapshot,
            feasibility_snapshot=feasibility_snapshot,
            recommendations_snapshot=recommendations_snapshot,
            optimization_snapshot=optimization_snapshot,
        )

        self.repository.create_planner_run(planner_run)
        self.repository.flush()
        self.session.commit()

        return planner_run

    def get_owned_run(
        self,
        *,
        planner_run_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        return self.repository.get_owned_planner_run_by_id(
            planner_run_id=planner_run_id,
            user_id=user_id,
        )

    def list_user_runs(
        self,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[PlannerRun]:
        if user_id < 1:
            raise ValueError("user_id must be positive")
        if skip < 0:
            raise ValueError("skip must be zero or greater")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        return self.repository.list_user_planner_runs(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    def list_trip_runs(
        self,
        *,
        trip_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[PlannerRun]:
        if trip_id < 1 or user_id < 1:
            raise ValueError("trip_id and user_id must be positive")
        if skip < 0:
            raise ValueError("skip must be zero or greater")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        return self.repository.list_trip_planner_runs(
            trip_id=trip_id,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    def get_latest_trip_run(
        self,
        *,
        trip_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        return self.repository.get_latest_for_trip(
            trip_id=trip_id,
            user_id=user_id,
        )

    def get_latest_accepted_trip_run(
        self,
        *,
        trip_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        return self.repository.get_latest_accepted_for_trip(
            trip_id=trip_id,
            user_id=user_id,
        )

    def accept_run(
        self,
        *,
        planner_run_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        planner_run = self.repository.get_owned_planner_run_by_id(
            planner_run_id=planner_run_id,
            user_id=user_id,
        )

        if planner_run is None:
            return None

        if planner_run.status == PlannerRunStatus.ACCEPTED:
            return planner_run

        if planner_run.status == PlannerRunStatus.REJECTED:
            raise ValueError("rejected planner run cannot be accepted")

        if planner_run.status == PlannerRunStatus.SUPERSEDED:
            raise ValueError("superseded planner run cannot be accepted")

        updated = self.repository.update_status(
            planner_run_id=planner_run_id,
            user_id=user_id,
            status=PlannerRunStatus.ACCEPTED,
        )

        if updated is None:
            return None

        if updated.trip_id is not None:
            self.repository.supersede_other_trip_runs(
                trip_id=updated.trip_id,
                user_id=user_id,
                accepted_run_id=updated.id,
            )

        self.repository.flush()
        self.session.commit()

        return updated

    def reject_run(
        self,
        *,
        planner_run_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        planner_run = self.repository.get_owned_planner_run_by_id(
            planner_run_id=planner_run_id,
            user_id=user_id,
        )

        if planner_run is None:
            return None

        if planner_run.status == PlannerRunStatus.ACCEPTED:
            raise ValueError("accepted planner run cannot be rejected")

        if planner_run.status == PlannerRunStatus.SUPERSEDED:
            raise ValueError("superseded planner run cannot be rejected")

        if planner_run.status == PlannerRunStatus.REJECTED:
            return planner_run

        updated = self.repository.update_status(
            planner_run_id=planner_run_id,
            user_id=user_id,
            status=PlannerRunStatus.REJECTED,
        )

        if updated is None:
            return None

        self.repository.flush()
        self.session.commit()

        return updated

    def update_evidence(
        self,
        *,
        planner_run_id: int,
        user_id: int,
        feasibility_score: int | None,
        feasibility_snapshot: dict,
        recommendations_snapshot: dict,
        optimization_snapshot: dict,
    ) -> PlannerRun | None:
        self._validate_feasibility_score(feasibility_score)

        planner_run = self.repository.get_owned_planner_run_by_id(
            planner_run_id=planner_run_id,
            user_id=user_id,
        )

        if planner_run is None:
            return None

        if planner_run.status in {
            PlannerRunStatus.REJECTED,
            PlannerRunStatus.SUPERSEDED,
        }:
            raise ValueError(
                "evidence cannot be updated for "
                "rejected or superseded planner runs"
            )

        updated = self.repository.update_evidence(
            planner_run_id=planner_run_id,
            user_id=user_id,
            feasibility_score=feasibility_score,
            feasibility_snapshot=feasibility_snapshot,
            recommendations_snapshot=recommendations_snapshot,
            optimization_snapshot=optimization_snapshot,
        )

        if updated is None:
            return None

        self.repository.flush()
        self.session.commit()

        return updated

    @staticmethod
    def _validate_feasibility_score(
        feasibility_score: int | None,
    ) -> None:
        if (
            feasibility_score is not None
            and not 0 <= feasibility_score <= 100
        ):
            raise ValueError(
                "feasibility_score must be between 0 and 100"
            )

    def rollback(self) -> None:
        self.session.rollback()
