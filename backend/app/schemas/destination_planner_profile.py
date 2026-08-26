from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.models.destination_planner_profile import (
    PlannerAccessStatus,
    PlannerRoadAccess,
    PlannerRoadCondition,
    PlannerRoadSurface,
    PlannerVerificationStatus,
)


class DestinationPlannerProfileBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended_visit_minutes: int | None = Field(
        default=None,
        gt=0,
    )
    minimum_visit_minutes: int | None = Field(
        default=None,
        gt=0,
    )
    maximum_visit_minutes: int | None = Field(
        default=None,
        gt=0,
    )

    opening_hours: dict[str, Any] = Field(default_factory=dict)

    opening_hours_timezone: str = Field(
        default="Africa/Tripoli",
        min_length=1,
        max_length=100,
    )

    access_status: PlannerAccessStatus = (
        PlannerAccessStatus.UNKNOWN
    )
    road_access: PlannerRoadAccess = PlannerRoadAccess.UNKNOWN
    road_surface: PlannerRoadSurface = PlannerRoadSurface.UNKNOWN
    road_condition: PlannerRoadCondition = (
        PlannerRoadCondition.UNKNOWN
    )

    planner_priority: int = Field(default=50, ge=0, le=100)
    meal_suitability: int = Field(default=0, ge=0, le=100)
    rest_suitability: int = Field(default=0, ge=0, le=100)

    data_source: str | None = Field(
        default=None,
        max_length=250,
    )

    verification_status: PlannerVerificationStatus = (
        PlannerVerificationStatus.UNVERIFIED
    )

    @model_validator(mode="after")
    def validate_visit_duration_range(
        self,
    ) -> "DestinationPlannerProfileBase":
        minimum = self.minimum_visit_minutes
        recommended = self.recommended_visit_minutes
        maximum = self.maximum_visit_minutes

        if (
            minimum is not None
            and recommended is not None
            and minimum > recommended
        ):
            raise ValueError(
                "minimum_visit_minutes cannot exceed "
                "recommended_visit_minutes"
            )

        if (
            maximum is not None
            and recommended is not None
            and maximum < recommended
        ):
            raise ValueError(
                "maximum_visit_minutes cannot be below "
                "recommended_visit_minutes"
            )

        if (
            minimum is not None
            and maximum is not None
            and minimum > maximum
        ):
            raise ValueError(
                "minimum_visit_minutes cannot exceed "
                "maximum_visit_minutes"
            )

        return self


class DestinationPlannerProfileCreate(
    DestinationPlannerProfileBase
):
    destination_id: int = Field(gt=0)


class DestinationPlannerProfileCreateRequest(
    DestinationPlannerProfileBase
):
    """HTTP payload for a destination-scoped planner profile route."""


class DestinationPlannerProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended_visit_minutes: int | None = Field(
        default=None,
        gt=0,
    )
    minimum_visit_minutes: int | None = Field(
        default=None,
        gt=0,
    )
    maximum_visit_minutes: int | None = Field(
        default=None,
        gt=0,
    )

    opening_hours: dict[str, Any] | None = None

    opening_hours_timezone: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    access_status: PlannerAccessStatus | None = None
    road_access: PlannerRoadAccess | None = None
    road_surface: PlannerRoadSurface | None = None
    road_condition: PlannerRoadCondition | None = None

    planner_priority: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    meal_suitability: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    rest_suitability: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    data_source: str | None = Field(
        default=None,
        max_length=250,
    )

    verification_status: PlannerVerificationStatus | None = None


class DestinationPlannerProfileRead(
    DestinationPlannerProfileBase
):
    id: int
    destination_id: int
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )
