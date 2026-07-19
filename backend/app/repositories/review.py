from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.sql.elements import ColumnElement

from app.models.destination import Destination
from app.models.review import Review, ReviewStatus
from app.repositories.base import BaseRepository
from app.repositories.sorting import safe_order_by
from app.schemas.review import ReviewSortField, ReviewSortOrder


class ReviewRepository(BaseRepository[Review]):
    @staticmethod
    def _build_filters(
        *,
        destination_id: int | None,
        status: ReviewStatus | None,
        rating: int | None,
        is_verified: bool | None,
    ) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = []
        if destination_id is not None:
            filters.append(Review.destination_id == destination_id)
        if status is not None:
            filters.append(Review.status == status)
        if rating is not None:
            filters.append(Review.rating == rating)
        if is_verified is not None:
            filters.append(Review.is_verified == is_verified)
        return filters

    def get_by_id(self, review_id: int) -> Review | None:
        return self.session.scalar(select(Review).where(Review.id == review_id))

    def get_approved_by_id(self, review_id: int) -> Review | None:
        return self.session.scalar(
            select(Review).where(
                Review.id == review_id,
                Review.status == ReviewStatus.APPROVED,
            )
        )

    def destination_exists(self, destination_id: int) -> bool:
        return self.session.scalar(
            select(Destination.id).where(Destination.id == destination_id).limit(1)
        ) is not None

    def list(
        self,
        *,
        skip: int,
        limit: int,
        destination_id: int | None,
        status: ReviewStatus | None,
        rating: int | None,
        is_verified: bool | None,
        sort_by: ReviewSortField,
        sort_order: ReviewSortOrder,
    ) -> Sequence[Review]:
        filters = self._build_filters(
            destination_id=destination_id,
            status=status,
            rating=rating,
            is_verified=is_verified,
        )
        ordering = safe_order_by(
            sort_by,
            sort_order,
            {
                "id": Review.id,
                "rating": Review.rating,
                "status": Review.status,
                "created_at": Review.created_at,
                "published_at": Review.published_at,
            },
        )
        statement = select(Review).where(*filters).order_by(ordering).offset(skip).limit(limit)
        return self.session.scalars(statement).all()

    def count(
        self,
        *,
        destination_id: int | None,
        status: ReviewStatus | None,
        rating: int | None,
        is_verified: bool | None,
    ) -> int:
        filters = self._build_filters(
            destination_id=destination_id,
            status=status,
            rating=rating,
            is_verified=is_verified,
        )
        statement: Select[tuple[int]] = select(func.count(Review.id)).where(*filters)
        return self.session.scalar(statement) or 0

    def list_approved_by_destination(
        self,
        *,
        destination_id: int,
        skip: int,
        limit: int,
    ) -> Sequence[Review]:
        return self.session.scalars(
            select(Review)
            .where(
                Review.destination_id == destination_id,
                Review.status == ReviewStatus.APPROVED,
            )
            .order_by(Review.published_at.desc(), Review.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()

    def count_approved_by_destination(self, destination_id: int) -> int:
        return self.session.scalar(
            select(func.count(Review.id)).where(
                Review.destination_id == destination_id,
                Review.status == ReviewStatus.APPROVED,
            )
        ) or 0
