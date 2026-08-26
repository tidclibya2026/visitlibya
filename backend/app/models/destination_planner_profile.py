from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
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
    from app.models.destination import Destination


class PlannerAccessStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    OPEN = "open"
    RESTRICTED = "restricted"
    SEASONAL = "seasonal"
    CLOSED = "closed"


class PlannerRoadAccess(str, enum.Enum):
    UNKNOWN = "unknown"
    STANDARD = "standard"
    FOUR_WHEEL_DRIVE = "four_wheel_drive"
    GUIDED_ONLY = "guided_only"


class PlannerRoadSurface(str, enum.Enum):
    UNKNOWN = "unknown"
    PAVED = "paved"
    MIXED = "mixed"
    UNPAVED = "unpaved"
    OFF_ROAD = "off_road"


class PlannerRoadCondition(str, enum.Enum):
    UNKNOWN = "unknown"
    GOOD = "good"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    VERY_DIFFICULT = "very_difficult"


class PlannerVerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    REVIEWED = "reviewed"
    VERIFIED = "verified"


class DestinationPlannerProfile(TimestampMixin, Base):
    __tablename__ = "destination_planner_profiles"

    __table_args__ = (
        CheckConstraint(
            "recommended_visit_minutes IS NULL "
            "OR recommended_visit_minutes > 0",
            name="destination_planner_recommended_visit_positive",
        ),
        CheckConstraint(
            "minimum_visit_minutes IS NULL "
            "OR minimum_visit_minutes > 0",
            name="destination_planner_minimum_visit_positive",
        ),
        CheckConstraint(
            "maximum_visit_minutes IS NULL "
            "OR maximum_visit_minutes > 0",
            name="destination_planner_maximum_visit_positive",
        ),
        CheckConstraint(
            "minimum_visit_minutes IS NULL "
            "OR recommended_visit_minutes IS NULL "
            "OR minimum_visit_minutes <= recommended_visit_minutes",
            name="destination_planner_minimum_not_above_recommended",
        ),
        CheckConstraint(
            "maximum_visit_minutes IS NULL "
            "OR recommended_visit_minutes IS NULL "
            "OR maximum_visit_minutes >= recommended_visit_minutes",
            name="destination_planner_maximum_not_below_recommended",
        ),
        CheckConstraint(
            "minimum_visit_minutes IS NULL "
            "OR maximum_visit_minutes IS NULL "
            "OR minimum_visit_minutes <= maximum_visit_minutes",
            name="destination_planner_visit_range_valid",
        ),
        CheckConstraint(
            "planner_priority >= 0 AND planner_priority <= 100",
            name="destination_planner_priority_range",
        ),
        CheckConstraint(
            "meal_suitability >= 0 AND meal_suitability <= 100",
            name="destination_planner_meal_suitability_range",
        ),
        CheckConstraint(
            "rest_suitability >= 0 AND rest_suitability <= 100",
            name="destination_planner_rest_suitability_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    recommended_visit_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    minimum_visit_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    maximum_visit_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    opening_hours: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        default=dict,
        nullable=False,
    )

    opening_hours_timezone: Mapped[str] = mapped_column(
        String(100),
        default="Africa/Tripoli",
        server_default="Africa/Tripoli",
        nullable=False,
    )

    access_status: Mapped[PlannerAccessStatus] = mapped_column(
        Enum(
            PlannerAccessStatus,
            name="planner_access_status",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PlannerAccessStatus.UNKNOWN,
        server_default=PlannerAccessStatus.UNKNOWN.value,
        nullable=False,
    )

    road_access: Mapped[PlannerRoadAccess] = mapped_column(
        Enum(
            PlannerRoadAccess,
            name="planner_road_access",
            native_enum=False,
            length=30,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PlannerRoadAccess.UNKNOWN,
        server_default=PlannerRoadAccess.UNKNOWN.value,
        nullable=False,
    )

    road_surface: Mapped[PlannerRoadSurface] = mapped_column(
        Enum(
            PlannerRoadSurface,
            name="planner_road_surface",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PlannerRoadSurface.UNKNOWN,
        server_default=PlannerRoadSurface.UNKNOWN.value,
        nullable=False,
    )

    road_condition: Mapped[PlannerRoadCondition] = mapped_column(
        Enum(
            PlannerRoadCondition,
            name="planner_road_condition",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PlannerRoadCondition.UNKNOWN,
        server_default=PlannerRoadCondition.UNKNOWN.value,
        nullable=False,
    )

    planner_priority: Mapped[int] = mapped_column(
        Integer,
        default=50,
        server_default="50",
        nullable=False,
    )

    meal_suitability: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    rest_suitability: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    data_source: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    verification_status: Mapped[PlannerVerificationStatus] = mapped_column(
        Enum(
            PlannerVerificationStatus,
            name="planner_verification_status",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        default=PlannerVerificationStatus.UNVERIFIED,
        server_default=PlannerVerificationStatus.UNVERIFIED.value,
        nullable=False,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    destination: Mapped["Destination"] = relationship(
        back_populates="planner_profile",
    )
