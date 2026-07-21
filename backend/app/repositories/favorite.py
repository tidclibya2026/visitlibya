from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import joinedload, selectinload

from app.models.destination import Destination, DestinationStatus
from app.models.favorite import Favorite
from app.models.media import DestinationMedia
from app.repositories.base import BaseRepository


class FavoriteRepository(BaseRepository[Favorite]):
    @staticmethod
    def _response_options():
        return (
            joinedload(Favorite.destination).joinedload(Destination.category),
            joinedload(Favorite.destination).selectinload(Destination.translations),
            joinedload(Favorite.destination)
            .selectinload(Destination.media_items)
            .joinedload(DestinationMedia.media),
        )

    def get_by_user_and_destination(
        self,
        user_id: int,
        destination_id: int,
    ) -> Favorite | None:
        return self.session.scalar(
            select(Favorite)
            .options(*self._response_options())
            .where(
                Favorite.user_id == user_id,
                Favorite.destination_id == destination_id,
            )
        )

    def get_public_destination(self, destination_id: int) -> Destination | None:
        return self.session.scalar(
            select(Destination)
            .options(
                joinedload(Destination.category),
                selectinload(Destination.translations),
                selectinload(Destination.media_items).joinedload(
                    DestinationMedia.media
                ),
            )
            .where(
                Destination.id == destination_id,
                Destination.status == DestinationStatus.PUBLISHED,
                Destination.is_active.is_(True),
            )
        )

    def list_by_user(
        self,
        *,
        user_id: int,
        skip: int,
        limit: int,
    ) -> Sequence[Favorite]:
        return self.session.scalars(
            select(Favorite)
            .join(Favorite.destination)
            .options(*self._response_options())
            .where(
                Favorite.user_id == user_id,
                Destination.status == DestinationStatus.PUBLISHED,
                Destination.is_active.is_(True),
            )
            .order_by(Favorite.created_at.desc(), Favorite.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()

    def count_by_user(self, user_id: int) -> int:
        statement: Select[tuple[int]] = (
            select(func.count(Favorite.id))
            .join(Favorite.destination)
            .where(
                Favorite.user_id == user_id,
                Destination.status == DestinationStatus.PUBLISHED,
                Destination.is_active.is_(True),
            )
        )
        return self.session.scalar(statement) or 0
