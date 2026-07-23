from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.media import DestinationMedia
    from app.models.review import Review
    from app.models.favorite import Favorite
    from app.models.trip_item import TripItem


class DestinationStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Destination(TimestampMixin, Base):
    __tablename__ = "destinations"
    __table_args__ = (
        Index("idx_destinations_geometry", "geometry", postgresql_using="gist"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
        nullable=False,
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    status: Mapped[DestinationStatus] = mapped_column(
        Enum(
            DestinationStatus,
            name="destination_status",
            native_enum=False,
            length=30,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=DestinationStatus.DRAFT,
        server_default=DestinationStatus.DRAFT.value,
        index=True,
        nullable=False,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    geometry: Mapped[object | None] = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=False,
        ),
        nullable=True,
    )

    municipality: Mapped[str | None] = mapped_column(
        String(150),
        index=True,
        nullable=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(150),
        index=True,
        nullable=True,
    )

    priority_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        index=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        index=True,
        nullable=False,
    )

    category: Mapped["Category | None"] = relationship(
        back_populates="destinations",
        lazy="joined",
    )

    translations: Mapped[list["DestinationTranslation"]] = relationship(
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    media_items: Mapped[list["DestinationMedia"]] = relationship(
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="destination",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )

    trip_items: Mapped[list["TripItem"]] = relationship(
        back_populates="destination",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class DestinationTranslation(TimestampMixin, Base):
    __tablename__ = "destination_translations"

    __table_args__ = (
        UniqueConstraint(
            "destination_id",
            "language_code",
            name="uq_destination_translation_language",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    language_code: Mapped[str] = mapped_column(
        String(10),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    short_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    historical_background: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    visitor_information: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    accessibility_information: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    seo_title: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    seo_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    destination: Mapped["Destination"] = relationship(
        back_populates="translations",
    )
