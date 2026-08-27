from collections.abc import Sequence

from geoalchemy2 import Geography, Geometry
from sqlalchemy import Select, cast, func, select
from sqlalchemy.orm import Load, joinedload, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.category import Category
from app.models.destination import Destination, DestinationStatus
from app.repositories.base import BaseRepository


class DestinationRepository(BaseRepository[Destination]):

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

    def get_planner_authority_by_id(
        self,
        destination_id: int,
    ) -> Destination | None:
        statement = (
            select(Destination)
            .options(
                *self._load_options(),
                selectinload(Destination.planner_profile),
            )
            .where(Destination.id == destination_id)
        )
        return self.session.scalar(statement)

    def get_planner_authority_by_slug(
        self,
        slug: str,
    ) -> Destination | None:
        statement = (
            select(Destination)
            .options(
                *self._load_options(),
                selectinload(Destination.planner_profile),
            )
            .where(Destination.slug == slug)
        )
        return self.session.scalar(statement)

    def get_by_slug(self, slug: str) -> Destination | None:
        statement = (
            select(Destination)
            .options(*self._load_options())
            .where(Destination.slug == slug)
        )
        return self.session.scalar(statement)

    def get_public_by_slug(self, slug: str) -> Destination | None:
        statement = (
            select(Destination)
            .options(*self._load_options())
            .where(
                Destination.slug == slug,
                Destination.status == DestinationStatus.PUBLISHED,
                Destination.is_active.is_(True),
            )
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

    @staticmethod
    def _public_spatial_filters() -> Sequence[ColumnElement[bool]]:
        return [
            Destination.status == DestinationStatus.PUBLISHED,
            Destination.is_active.is_(True),
            Destination.geometry.is_not(None),
        ]

    def list_public_in_bbox(
        self,
        *,
        min_longitude: float,
        min_latitude: float,
        max_longitude: float,
        max_latitude: float,
        skip: int,
        limit: int,
    ) -> Sequence[Destination]:
        envelope = func.ST_MakeEnvelope(
            min_longitude,
            min_latitude,
            max_longitude,
            max_latitude,
            4326,
            type_=Geometry(geometry_type="POLYGON", srid=4326),
        )

        statement = (
            select(Destination)
            .options(*self._load_options())
            .where(
                *self._public_spatial_filters(),
                func.ST_Intersects(Destination.geometry, envelope),
            )
            .order_by(Destination.priority_order, Destination.id)
            .offset(skip)
            .limit(limit)
        )
        return self.session.scalars(statement).all()

    def count_public_in_bbox(
        self,
        *,
        min_longitude: float,
        min_latitude: float,
        max_longitude: float,
        max_latitude: float,
    ) -> int:
        envelope = func.ST_MakeEnvelope(
            min_longitude,
            min_latitude,
            max_longitude,
            max_latitude,
            4326,
            type_=Geometry(geometry_type="POLYGON", srid=4326),
        )

        statement: Select[tuple[int]] = (
            select(func.count(Destination.id))
            .where(
                *self._public_spatial_filters(),
                func.ST_Intersects(Destination.geometry, envelope),
            )
        )
        return self.session.scalar(statement) or 0

    def list_public_nearby(
        self,
        *,
        longitude: float,
        latitude: float,
        radius_meters: float,
        limit: int,
    ) -> Sequence[Destination]:
        point = func.ST_SetSRID(
            func.ST_MakePoint(longitude, latitude),
            4326,
            type_=Geometry(geometry_type="POINT", srid=4326),
        )

        destination_geography = cast(
            Destination.geometry,
            Geography(geometry_type="POINT", srid=4326),
        )
        point_geography = cast(
            point,
            Geography(geometry_type="POINT", srid=4326),
        )

        distance = func.ST_Distance(
            destination_geography,
            point_geography,
        )

        statement = (
            select(Destination)
            .options(*self._load_options())
            .where(
                *self._public_spatial_filters(),
                func.ST_DWithin(
                    destination_geography,
                    point_geography,
                    radius_meters,
                ),
            )
            .order_by(distance, Destination.priority_order, Destination.id)
            .limit(limit)
        )
        return self.session.scalars(statement).all()

    def refresh(self, destination: Destination) -> None:
        self.session.refresh(
            destination,
            attribute_names=["category", "translations"],
        )
