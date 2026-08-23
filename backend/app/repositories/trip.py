from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.orm import joinedload, noload, selectinload

from app.models.destination import Destination, DestinationStatus
from app.models.trip import Trip, TripVisibility
from app.models.trip_item import TripItem
from app.repositories.base import BaseRepository


@dataclass(frozen=True, slots=True)
class TripListEntry:
    trip: Trip
    item_count: int


class TripRepository(BaseRepository[Trip]):
    @staticmethod
    def _detail_options():
        return (
            selectinload(Trip.items)
            .joinedload(TripItem.destination)
            .selectinload(Destination.translations),
        )

    def create_trip(self, trip: Trip) -> None:
        self.add(trip)

    def get_owned_trip_by_id(self, trip_id: int, user_id: int) -> Trip | None:
        return self.session.scalar(
            select(Trip)
            .options(*self._detail_options())
            .where(Trip.id == trip_id, Trip.user_id == user_id)
        )

    def get_public_trip_by_id(self, trip_id: int) -> Trip | None:
        return self.session.scalar(
            select(Trip)
            .options(*self._detail_options())
            .where(
                Trip.id == trip_id,
                Trip.visibility == TripVisibility.PUBLIC,
            )
        )

    def get_unlisted_trip_by_token(self, share_token: str) -> Trip | None:
        return self.session.scalar(
            select(Trip)
            .options(*self._detail_options())
            .where(
                Trip.share_token == share_token,
                Trip.visibility == TripVisibility.UNLISTED,
            )
        )

    def list_user_trips(
        self, user_id: int, skip: int, limit: int
    ) -> Sequence[TripListEntry]:
        item_count = (
            select(func.count(TripItem.id))
            .where(TripItem.trip_id == Trip.id)
            .correlate(Trip)
            .scalar_subquery()
        )
        rows = self.session.execute(
            select(Trip, item_count.label("item_count"))
            .options(noload(Trip.items))
            .where(Trip.user_id == user_id)
            .order_by(Trip.created_at.desc(), Trip.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()
        return [TripListEntry(trip=trip, item_count=item_count) for trip, item_count in rows]

    def count_user_trips(self, user_id: int) -> int:
        return self.session.scalar(
            select(func.count(Trip.id)).where(Trip.user_id == user_id)
        ) or 0

    def count_trip_items(self, trip_id: int) -> int:
        return self.session.scalar(
            select(func.count(TripItem.id)).where(TripItem.trip_id == trip_id)
        ) or 0

    def delete_trip(self, trip: Trip) -> None:
        self.delete(trip)

    def get_trip_item_by_id(self, trip_id: int, item_id: int) -> TripItem | None:
        return self.session.scalar(
            select(TripItem).where(
                TripItem.id == item_id,
                TripItem.trip_id == trip_id,
            )
        )

    def list_trip_items(self, trip_id: int) -> Sequence[TripItem]:
        return self.session.scalars(
            select(TripItem)
            .options(
                joinedload(TripItem.destination).selectinload(
                    Destination.translations
                )
            )
            .where(TripItem.trip_id == trip_id)
            .order_by(TripItem.day_number, TripItem.sort_order, TripItem.id)
        ).all()

    def add_trip_item(self, item: TripItem) -> None:
        self.session.add(item)

    def delete_trip_item(self, item: TripItem) -> None:
        self.session.delete(item)

    def get_public_destination(self, destination_id: int) -> Destination | None:
        return self.session.scalar(
            select(Destination)
            .options(selectinload(Destination.translations))
            .where(
                Destination.id == destination_id,
                Destination.status == DestinationStatus.PUBLISHED,
                Destination.is_active.is_(True),
            )
        )

    def next_sort_order(self, trip_id: int, day_number: int) -> int:
        maximum = self.session.scalar(
            select(func.max(TripItem.sort_order)).where(
                TripItem.trip_id == trip_id,
                TripItem.day_number == day_number,
            )
        )
        return (maximum if maximum is not None else -1) + 1

    def max_sort_order(self, trip_id: int) -> int:
        maximum = self.session.scalar(
            select(func.max(TripItem.sort_order)).where(TripItem.trip_id == trip_id)
        )
        return maximum if maximum is not None else -1

    def increment_trip_version(
        self,
        trip_id: int,
        user_id: int,
        expected_version: int,
    ) -> int | None:
        return self.session.scalar(
            update(Trip)
            .where(
                Trip.id == trip_id,
                Trip.user_id == user_id,
                Trip.version == expected_version,
            )
            .values(version=Trip.version + 1)
            .returning(Trip.version)
        )
