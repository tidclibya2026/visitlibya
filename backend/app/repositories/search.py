from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Subquery

from app.models.destination import Destination, DestinationStatus, DestinationTranslation
from app.models.media import DestinationMedia, MediaAsset
from app.models.review import Review, ReviewStatus
from app.repositories.sorting import safe_order_by
from app.schemas.search import SearchFilters, SearchSortField, SearchSortOrder


@dataclass(frozen=True)
class SearchResultRow:
    destination: Destination
    average_rating: float | None
    reviews_count: int
    primary_media_url: str | None


class SearchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _review_aggregate() -> Subquery:
        return (
            select(
                Review.destination_id.label("destination_id"),
                func.avg(Review.rating).label("average_rating"),
                func.count(Review.id).label("reviews_count"),
            )
            .where(Review.status == ReviewStatus.APPROVED)
            .group_by(Review.destination_id)
            .subquery("approved_review_aggregate")
        )

    @staticmethod
    def _primary_media_aggregate() -> Subquery:
        media_url = func.coalesce(MediaAsset.public_url, MediaAsset.file_path)
        ranked_media = (
            select(
                DestinationMedia.destination_id.label("destination_id"),
                media_url.label("primary_media_url"),
                func.row_number()
                .over(
                    partition_by=DestinationMedia.destination_id,
                    order_by=(
                        DestinationMedia.created_at.desc(),
                        DestinationMedia.id.desc(),
                    ),
                )
                .label("media_rank"),
            )
            .join(MediaAsset, MediaAsset.id == DestinationMedia.media_id)
            .where(
                DestinationMedia.is_primary.is_(True),
                MediaAsset.is_active.is_(True),
            )
            .subquery("ranked_primary_media")
        )
        return (
            select(
                ranked_media.c.destination_id,
                ranked_media.c.primary_media_url,
            )
            .where(ranked_media.c.media_rank == 1)
            .subquery("primary_media_aggregate")
        )

    @staticmethod
    def _name_sort_expression() -> ColumnElement[str | None]:
        return (
            select(func.min(DestinationTranslation.name))
            .where(DestinationTranslation.destination_id == Destination.id)
            .correlate(Destination)
            .scalar_subquery()
        )

    @classmethod
    def _build_filters(
        cls,
        filters: SearchFilters,
        review_aggregate: Subquery,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [
            Destination.status == DestinationStatus.PUBLISHED,
            Destination.is_active.is_(True),
        ]
        if filters.category_id is not None:
            conditions.append(Destination.category_id == filters.category_id)
        if filters.city is not None:
            conditions.append(Destination.municipality.ilike(filters.city.strip()))
        if filters.region is not None:
            conditions.append(Destination.region.ilike(filters.region.strip()))
        if filters.is_featured is not None:
            conditions.append(Destination.is_featured == filters.is_featured)
        if filters.minimum_rating is not None:
            conditions.append(
                review_aggregate.c.average_rating >= filters.minimum_rating
            )
        if filters.maximum_rating is not None:
            conditions.append(
                review_aggregate.c.average_rating <= filters.maximum_rating
            )
        if filters.q is not None and (query := filters.q.strip()):
            pattern = f"%{query}%"
            translation_match = exists(
                select(DestinationTranslation.id).where(
                    DestinationTranslation.destination_id == Destination.id,
                    or_(
                        DestinationTranslation.name.ilike(pattern),
                        DestinationTranslation.short_description.ilike(pattern),
                        DestinationTranslation.description.ilike(pattern),
                    ),
                )
            )
            conditions.append(
                or_(
                    Destination.slug.ilike(pattern),
                    Destination.municipality.ilike(pattern),
                    Destination.region.ilike(pattern),
                    translation_match,
                )
            )
        return conditions

    def search(
        self,
        *,
        filters: SearchFilters,
        offset: int,
        limit: int,
        sort_by: SearchSortField,
        sort_order: SearchSortOrder,
    ) -> tuple[Sequence[SearchResultRow], int]:
        review_aggregate = self._review_aggregate()
        media_aggregate = self._primary_media_aggregate()
        conditions = self._build_filters(filters, review_aggregate)
        average_rating = review_aggregate.c.average_rating
        reviews_count = func.coalesce(review_aggregate.c.reviews_count, 0)
        ordering = safe_order_by(
            sort_by,
            sort_order,
            {
                "name": self._name_sort_expression(),
                "created_at": Destination.created_at,
                "updated_at": Destination.updated_at,
                "average_rating": average_rating,
                "reviews_count": reviews_count,
            },
        )
        if sort_by == "average_rating":
            ordering = ordering.nulls_last()
        statement = (
            select(
                Destination,
                average_rating,
                reviews_count.label("reviews_count"),
                media_aggregate.c.primary_media_url,
            )
            .options(
                joinedload(Destination.category),
                selectinload(Destination.translations),
            )
            .outerjoin(
                review_aggregate,
                review_aggregate.c.destination_id == Destination.id,
            )
            .outerjoin(
                media_aggregate,
                media_aggregate.c.destination_id == Destination.id,
            )
            .where(*conditions)
            .order_by(ordering, Destination.id)
            .offset(offset)
            .limit(limit)
        )
        count_statement: Select[tuple[int]] = (
            select(func.count(func.distinct(Destination.id)))
            .outerjoin(
                review_aggregate,
                review_aggregate.c.destination_id == Destination.id,
            )
            .where(*conditions)
        )
        rows = self.session.execute(statement).all()
        total = self.session.scalar(count_statement) or 0
        return (
            [
                SearchResultRow(
                    destination=row[0],
                    average_rating=float(row[1]) if row[1] is not None else None,
                    reviews_count=int(row[2]),
                    primary_media_url=row[3],
                )
                for row in rows
            ],
            total,
        )
