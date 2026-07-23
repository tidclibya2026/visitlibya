from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.trip_item import TripItem
    from app.models.user import User


class TripStatus(str, enum.Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TripVisibility(str, enum.Enum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="trip_date_range",
        ),
        Index("ix_trips_user_created_at", "user_id", "created_at"),
        Index("ix_trips_user_start_date", "user_id", "start_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[TripStatus] = mapped_column(
        Enum(
            TripStatus,
            name="trip_status",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=TripStatus.DRAFT,
        server_default=TripStatus.DRAFT.value,
        nullable=False,
    )
    visibility: Mapped[TripVisibility] = mapped_column(
        Enum(
            TripVisibility,
            name="trip_visibility",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=TripVisibility.PRIVATE,
        server_default=TripVisibility.PRIVATE.value,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="trips")
    items: Mapped[list["TripItem"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(TripItem.day_number, TripItem.sort_order, TripItem.id)",
        lazy="selectin",
    )
