from collections.abc import Sequence

from sqlalchemy import select, update

from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.models.trip import Trip
from app.repositories.base import BaseRepository


class PlannerRunRepository(BaseRepository[PlannerRun]):
    def owned_trip_exists(self, trip_id: int, user_id: int) -> bool:
        return self.session.scalar(
            select(Trip.id)
            .where(Trip.id == trip_id, Trip.user_id == user_id)
            .limit(1)
        ) is not None

    def lock_owned_trip(self, trip_id: int, user_id: int) -> bool:
        return self.session.scalar(
            select(Trip.id)
            .where(Trip.id == trip_id, Trip.user_id == user_id)
            .with_for_update()
        ) is not None

    def create_planner_run(self, planner_run: PlannerRun) -> None:
        self.add(planner_run)

    def get_owned_planner_run_by_id(
        self,
        planner_run_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        return self.session.scalar(
            select(PlannerRun).where(
                PlannerRun.id == planner_run_id,
                PlannerRun.user_id == user_id,
            )
        )

    def list_user_planner_runs(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[PlannerRun]:
        return self.session.scalars(
            select(PlannerRun)
            .where(PlannerRun.user_id == user_id)
            .order_by(
                PlannerRun.created_at.desc(),
                PlannerRun.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        ).all()

    def list_trip_planner_runs(
        self,
        trip_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[PlannerRun]:
        return self.session.scalars(
            select(PlannerRun)
            .where(
                PlannerRun.trip_id == trip_id,
                PlannerRun.user_id == user_id,
            )
            .order_by(
                PlannerRun.created_at.desc(),
                PlannerRun.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        ).all()

    def get_latest_for_trip(
        self,
        trip_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        return self.session.scalar(
            select(PlannerRun)
            .where(
                PlannerRun.trip_id == trip_id,
                PlannerRun.user_id == user_id,
            )
            .order_by(
                PlannerRun.created_at.desc(),
                PlannerRun.id.desc(),
            )
            .limit(1)
        )

    def get_latest_accepted_for_trip(
        self,
        trip_id: int,
        user_id: int,
    ) -> PlannerRun | None:
        return self.session.scalar(
            select(PlannerRun)
            .where(
                PlannerRun.trip_id == trip_id,
                PlannerRun.user_id == user_id,
                PlannerRun.status == PlannerRunStatus.ACCEPTED,
            )
            .order_by(
                PlannerRun.created_at.desc(),
                PlannerRun.id.desc(),
            )
            .limit(1)
        )

    def update_status(
        self,
        planner_run_id: int,
        user_id: int,
        status: PlannerRunStatus,
    ) -> PlannerRun | None:
        return self.session.scalar(
            update(PlannerRun)
            .where(
                PlannerRun.id == planner_run_id,
                PlannerRun.user_id == user_id,
            )
            .values(status=status)
            .returning(PlannerRun)
        )

    def supersede_other_trip_runs(
        self,
        trip_id: int,
        user_id: int,
        accepted_run_id: int,
    ) -> Sequence[int]:
        return self.session.scalars(
            update(PlannerRun)
            .where(
                PlannerRun.trip_id == trip_id,
                PlannerRun.user_id == user_id,
                PlannerRun.id != accepted_run_id,
                PlannerRun.status.in_(
                    (
                        PlannerRunStatus.GENERATED,
                        PlannerRunStatus.ACCEPTED,
                    )
                ),
            )
            .values(status=PlannerRunStatus.SUPERSEDED)
            .returning(PlannerRun.id)
        ).all()

    def update_evidence(
        self,
        planner_run_id: int,
        user_id: int,
        *,
        feasibility_score: int | None,
        feasibility_snapshot: dict,
        recommendations_snapshot: dict,
        optimization_snapshot: dict,
    ) -> PlannerRun | None:
        return self.session.scalar(
            update(PlannerRun)
            .where(
                PlannerRun.id == planner_run_id,
                PlannerRun.user_id == user_id,
            )
            .values(
                feasibility_score=feasibility_score,
                feasibility_snapshot=feasibility_snapshot,
                recommendations_snapshot=recommendations_snapshot,
                optimization_snapshot=optimization_snapshot,
            )
            .returning(PlannerRun)
        )
