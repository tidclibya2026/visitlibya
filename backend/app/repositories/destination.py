from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Load, Session, joinedload, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.category import Category
from app.models.destination import Destination, DestinationStatus


class DestinationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _load_options() -> tuple[Load, Load]:
        return (
            joinedload(Destination.category),
            selectinload(Destination.translations),
        )

    @staticmethod
    def _build_filters(
        *,
        status: DestinationStatus | None,
        category_id: int | None,
        region: str | None,
        municipality: str | None,
        is_featured: bool | None,
        is_active: bool | None,
    ) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = []
        if status is not None:
            filters.append(Destination.status == status)
        if category_id is not None:
            filters.append(Destination.category_id == category_id)
        if region is not None:
            filters.append(Destination.region == region)
        if municipality is not None:
            filters.append(Destination.municipality == municipality)
        if is_featured is not None:
            filters.append(Destination.is_featured == is_featured)
        if is_active is not None:
            filters.append(Destination.is_active == is_active)
        return filters

    def get_by_id(self, destination_id: int) -> Destination | None:
        statement = (
            select(Destination)
            .options(*self._load_options())
            .where(Destination.id == destination_id)
        )
        return self.session.scalar(statement)

    def get_by_slug(self, slug: str) -> Destination | None:
        statement = (
            select(Destination)
            .options(*self._load_options())
            .where(Destination.slug == slug)
        )
        return self.session.scalar(statement)

    def slug_exists(
        self,
        slug: str,
        exclude_destination_id: int | None = None,
    ) -> bool:
        statement = select(Destination.id).where(Destination.slug == slug)
        if exclude_destination_id is not None:
            statement = statement.where(Destination.id != exclude_destination_id)
        return self.session.scalar(statement.limit(1)) is not None

    def category_exists(self, category_id: int) -> bool:
        statement = select(Category.id).where(Category.id == category_id).limit(1)
        return self.session.scalar(statement) is not None

    def list(
        self,
        *,
        skip: int,
        limit: int,
        status: DestinationStatus | None,
        category_id: int | None,
        region: str | None,
        municipality: str | None,
        is_featured: bool | None,
        is_active: bool | None,
    ) -> Sequence[Destination]:
        filters = self._build_filters(
            status=status,
            category_id=category_id,
            region=region,
            municipality=municipality,
            is_featured=is_featured,
            is_active=is_active,
        )
        statement = (
            select(Destination)
            .options(*self._load_options())
            .where(*filters)
            .order_by(Destination.priority_order, Destination.id)
            .offset(skip)
            .limit(limit)
        )
        return self.session.scalars(statement).all()

    def count(
        self,
        *,
        status: DestinationStatus | None,
        category_id: int | None,
        region: str | None,
        municipality: str | None,
        is_featured: bool | None,
        is_active: bool | None,
    ) -> int:
        filters = self._build_filters(
            status=status,
            category_id=category_id,
            region=region,
            municipality=municipality,
            is_featured=is_featured,
            is_active=is_active,
        )
        statement: Select[tuple[int]] = select(func.count(Destination.id)).where(
            *filters
        )
        return self.session.scalar(statement) or 0

    def add(self, destination: Destination) -> None:
        self.session.add(destination)

    def delete(self, destination: Destination) -> None:
        self.session.delete(destination)

    def flush(self) -> None:
        self.session.flush()

    def refresh(self, destination: Destination) -> None:
        self.session.refresh(
            destination,
            attribute_names=["category", "translations"],
        )
