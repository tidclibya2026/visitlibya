from sqlalchemy import select

from app.models.destination import Destination
from app.models.destination_planner_profile import DestinationPlannerProfile
from app.repositories.base import BaseRepository


class DestinationPlannerProfileRepository(
    BaseRepository[DestinationPlannerProfile]
):
    def destination_exists(self, destination_id: int) -> bool:
        statement = (
            select(Destination.id)
            .where(Destination.id == destination_id)
            .limit(1)
        )
        return self.session.scalar(statement) is not None

    def get_by_id(
        self,
        profile_id: int,
    ) -> DestinationPlannerProfile | None:
        return self.session.scalar(
            select(DestinationPlannerProfile).where(
                DestinationPlannerProfile.id == profile_id
            )
        )

    def get_by_destination_id(
        self,
        destination_id: int,
    ) -> DestinationPlannerProfile | None:
        return self.session.scalar(
            select(DestinationPlannerProfile).where(
                DestinationPlannerProfile.destination_id == destination_id
            )
        )

    def profile_exists_for_destination(
        self,
        destination_id: int,
    ) -> bool:
        statement = (
            select(DestinationPlannerProfile.id)
            .where(
                DestinationPlannerProfile.destination_id == destination_id
            )
            .limit(1)
        )
        return self.session.scalar(statement) is not None

    def create_profile(
        self,
        profile: DestinationPlannerProfile,
    ) -> None:
        self.add(profile)
