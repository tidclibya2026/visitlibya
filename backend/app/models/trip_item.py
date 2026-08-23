from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.destination import Destination
    from app.models.trip import Trip


class TripItem(TimestampMixin, Base):
    __tablename__ = "trip_items"
    __table_args__ = (
        CheckConstraint("day_number >= 1", name="day_number_positive"),
        CheckConstraint("sort_order >= 0", name="sort_order_nonnegative"),
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="duration_minutes_positive",
        ),
        UniqueConstraint(
            "trip_id",
            "day_number",
            "sort_order",
            name="uq_trip_items_trip_day_position",
        ),
        Index("ix_trip_items_trip_day_order", "trip_id", "day_number", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    trip: Mapped["Trip"] = relationship(back_populates="items")
    destination: Mapped["Destination"] = relationship(back_populates="trip_items", lazy="joined")
