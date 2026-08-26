from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


JSON_TYPE = JSON().with_variant(
    JSONB(),
    "postgresql",
)

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.user import User


class PlannerRunStatus(str, enum.Enum):
    GENERATED = "generated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class PlannerRun(TimestampMixin, Base):
    __tablename__ = "planner_runs"

    __table_args__ = (
        CheckConstraint(
            "planner_version >= 1",
            name="planner_run_version_positive",
        ),
        CheckConstraint(
            "feasibility_score IS NULL OR "
            "(feasibility_score >= 0 AND feasibility_score <= 100)",
            name="planner_run_feasibility_range",
        ),
        Index(
            "ix_planner_runs_trip_created_at",
            "trip_id",
            "created_at",
        ),
        Index(
            "ix_planner_runs_user_created_at",
            "user_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    trip_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "trips.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    planner_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    engine_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="visitlibya-ai-planner-v1",
        server_default="visitlibya-ai-planner-v1",
    )

    status: Mapped[PlannerRunStatus] = mapped_column(
        Enum(
            PlannerRunStatus,
            name="planner_run_status",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [
                item.value
                for item in enum_class
            ],
        ),
        nullable=False,
        default=PlannerRunStatus.GENERATED,
        server_default=PlannerRunStatus.GENERATED.value,
    )

    feasibility_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    input_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )

    itinerary_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )

    feasibility_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )

    recommendations_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )

    optimization_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )

    trip: Mapped["Trip | None"] = relationship()

    user: Mapped["User"] = relationship()
